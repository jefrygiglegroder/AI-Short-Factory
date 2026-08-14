"""
Hardware detection utilities for AI Short Factory.

This module detects GPU(s) (NVIDIA), VRAM, CUDA availability/version, current VRAM usage
(if available), CPU info, system RAM, and disk space. It prefers pynvml when installed,
but falls back to parsing nvidia-smi output when needed. All functions are designed
to fail gracefully when NVIDIA tooling is unavailable (CPU-only machines).

Type hints and a small dataclass are provided for clarity. No external side-effects.

Functions:
- get_gpu_info() -> list[GPUInfo]
- get_cpu_info() -> dict
- get_system_info() -> dict
- detect_hardware() -> dict
- pretty_print_hardware() -> str

This file is part of PHASE 1: hardware detection foundation.
"""
from __future__ import annotations

import dataclasses
import json
import platform
import re
import shutil
import subprocess
from typing import Dict, List, Optional

try:
    import psutil
except Exception:  # pragma: no cover - psutil may not be present in some CI
    psutil = None


@dataclasses.dataclass
class GPUInfo:
    index: int
    name: str
    total_vram_bytes: Optional[int]
    free_vram_bytes: Optional[int]
    used_vram_bytes: Optional[int]
    cuda_driver_version: Optional[str]
    uuid: Optional[str]

    def total_vram_gb(self) -> Optional[float]:
        return None if self.total_vram_bytes is None else round(self.total_vram_bytes / (1024 ** 3), 2)

    def free_vram_gb(self) -> Optional[float]:
        return None if self.free_vram_bytes is None else round(self.free_vram_bytes / (1024 ** 3), 2)

    def used_vram_gb(self) -> Optional[float]:
        return None if self.used_vram_bytes is None else round(self.used_vram_bytes / (1024 ** 3), 2)


def _bytes_to_human(n: int) -> str:
    # simple human readable converter
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if n < 1024.0:
            return f"{n:3.1f}{unit}"
        n /= 1024.0
    return f"{n:.1f}PB"


def _try_pynvml() -> Optional[List[GPUInfo]]:
    """Attempt to gather GPU info using pynvml (preferred).
    Returns None on failure.
    """
    try:
        import pynvml  # type: ignore
    except Exception:
        return None

    try:
        pynvml.nvmlInit()
        device_count = pynvml.nvmlDeviceGetCount()
        gpus: List[GPUInfo] = []
        for i in range(device_count):
            handle = pynvml.nvmlDeviceGetHandleByIndex(i)
            name = pynvml.nvmlDeviceGetName(handle).decode("utf-8") if isinstance(pynvml.nvmlDeviceGetName(handle), bytes) else str(pynvml.nvmlDeviceGetName(handle))
            try:
                mem = pynvml.nvmlDeviceGetMemoryInfo(handle)
                total = int(mem.total)
                free = int(mem.free)
                used = int(mem.used)
            except Exception:
                total = free = used = None

            try:
                uuid = pynvml.nvmlDeviceGetUUID(handle).decode("utf-8") if isinstance(pynvml.nvmlDeviceGetUUID(handle), bytes) else str(pynvml.nvmlDeviceGetUUID(handle))
            except Exception:
                uuid = None

            # driver/cuda version can be read from system though pynvml has limited cross-platform support
            try:
                drv = pynvml.nvmlSystemGetDriverVersion()
                drv = drv.decode("utf-8") if isinstance(drv, bytes) else str(drv)
            except Exception:
                drv = None

            gpus.append(GPUInfo(index=i, name=name, total_vram_bytes=total, free_vram_bytes=free, used_vram_bytes=used, cuda_driver_version=drv, uuid=uuid))

        try:
            pynvml.nvmlShutdown()
        except Exception:
            pass

        return gpus
    except Exception:
        return None


def _try_nvidia_smi() -> Optional[List[GPUInfo]]:
    """Fallback: call nvidia-smi and parse CSV output. Returns None if nvidia-smi is not available.
    """
    try:
        # Query a set of fields that are broadly supported
        query_fields = [
            "index",
            "name",
            "memory.total",
            "memory.used",
            "memory.free",
            "driver_version",
            "uuid",
        ]
        cmd = [
            "nvidia-smi",
            f"--query-gpu={','.join(query_fields)}",
            "--format=csv,noheader,nounits",
        ]
        output = subprocess.check_output(cmd, encoding="utf-8", errors="replace")
    except Exception:
        return None

    gpus: List[GPUInfo] = []
    for line in output.strip().splitlines():
        parts = [p.strip() for p in line.split(",")]
        if len(parts) < 7:
            # unexpected format, skip
            continue
        try:
            idx = int(parts[0])
        except Exception:
            idx = 0
        name = parts[1]
        def to_bytes(x: str) -> Optional[int]:
            try:
                return int(float(x) * 1024 * 1024)
            except Exception:
                return None
        total = to_bytes(parts[2])
        used = to_bytes(parts[3])
        free = to_bytes(parts[4])
        drv = parts[5] if parts[5] else None
        uuid = parts[6] if parts[6] else None
        gpus.append(GPUInfo(index=idx, name=name, total_vram_bytes=total, free_vram_bytes=free, used_vram_bytes=used, cuda_driver_version=drv, uuid=uuid))

    return gpus


def get_gpu_info() -> List[GPUInfo]:
    """Get a list of detected GPUs. Returns empty list if none detected or on failure.

    The function tries pynvml first, then nvidia-smi, and finally returns an empty list when
    no NVIDIA GPU information is available.

    Guarantees: returns a list (possibly empty) and never raises for expected failures.
    """
    gpus = _try_pynvml()
    if gpus is not None:
        return gpus
    gpus = _try_nvidia_smi()
    if gpus is not None:
        return gpus
    return []


def get_cpu_info() -> Dict[str, Optional[str]]:
    """Return CPU and RAM information as a dictionary.

    Keys: processor, physical_cores, logical_cores, total_ram_bytes
    """
    info: Dict[str, Optional[str]] = {}
    info["processor"] = platform.processor() or platform.machine() or None
    try:
        info["physical_cores"] = str(psutil.cpu_count(logical=False)) if psutil else None
        info["logical_cores"] = str(psutil.cpu_count(logical=True)) if psutil else None
    except Exception:
        info["physical_cores"] = info["logical_cores"] = None

    try:
        info["total_ram_bytes"] = str(psutil.virtual_memory().total) if psutil else None
    except Exception:
        info["total_ram_bytes"] = None

    return info


def get_system_info() -> Dict[str, Optional[str]]:
    """Return consolidated system info: CPU, RAM, disk usage, GPUs and a small summary.

    This is a higher level convenience wrapper used by CLI or UI.
    """
    gpus = get_gpu_info()
    cpu = get_cpu_info()
    try:
        if psutil:
            disk = psutil.disk_usage(".")
            disk_total = disk.total
            disk_free = disk.free
            disk_used = disk.used
        else:
            du = shutil.disk_usage(".")
            disk_total = du.total
            disk_free = du.free
            disk_used = du.used
    except Exception:
        disk_total = disk_free = disk_used = None

    summary = {
        "gpus": [dataclasses.asdict(g) for g in gpus],
        "cpu": cpu,
        "disk_total_bytes": disk_total,
        "disk_free_bytes": disk_free,
        "disk_used_bytes": disk_used,
    }
    return summary


def pretty_print_hardware() -> str:
    """Return a human-readable string describing detected hardware.

    This is useful for CLI output or a simple UI card.
    """
    info = get_system_info()
    lines: List[str] = []
    gpus = info.get("gpus", []) or []
    if gpus:
        lines.append(f"GPUs detected: {len(gpus)}")
        for g in gpus:
            name = g.get("name") if isinstance(g, dict) else getattr(g, "name", "Unknown")
            total = g.get("total_vram_bytes") if isinstance(g, dict) else getattr(g, "total_vram_bytes", None)
            used = g.get("used_vram_bytes") if isinstance(g, dict) else getattr(g, "used_vram_bytes", None)
            drv = g.get("cuda_driver_version") if isinstance(g, dict) else getattr(g, "cuda_driver_version", None)
            uuid = g.get("uuid") if isinstance(g, dict) else getattr(g, "uuid", None)
            if total is not None:
                lines.append(f"  - {name} ({_bytes_to_human(total)} total)")
                if used is not None:
                    lines.append(f"      used: {_bytes_to_human(used)}")
                if drv:
                    lines.append(f"      driver: {drv}")
                if uuid:
                    lines.append(f"      uuid: {uuid}")
            else:
                lines.append(f"  - {name} (memory: unknown)")
    else:
        lines.append("No NVIDIA GPUs detected (or tooling unavailable).")

    cpu = info.get("cpu", {}) or {}
    proc = cpu.get("processor")
    phys = cpu.get("physical_cores")
    logical = cpu.get("logical_cores")
    ram_b = cpu.get("total_ram_bytes")
    lines.append("")
    lines.append("CPU:")
    lines.append(f"  processor: {proc}")
    lines.append(f"  physical cores: {phys}")
    lines.append(f"  logical cores: {logical}")
    if ram_b:
        try:
            lines.append(f"  total RAM: {_bytes_to_human(int(ram_b))}")
        except Exception:
            lines.append(f"  total RAM: {ram_b}")

    dt = info.get("disk_total_bytes")
    df = info.get("disk_free_bytes")
    lines.append("")
    lines.append("Disk:")
    if dt is not None:
        lines.append(f"  total: {_bytes_to_human(dt)}")
    if df is not None:
        lines.append(f"  free: {_bytes_to_human(df)}")

    return "\n".join(lines)


if __name__ == "__main__":
    # simple CLI for quick testing
    print(pretty_print_hardware())
