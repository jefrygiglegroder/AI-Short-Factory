import pytest

from app.core import hardware


def test_get_cpu_info_without_psutil(monkeypatch):
    """Simulate missing psutil and ensure get_cpu_info returns the expected keys and doesn't raise."""
    monkeypatch.setattr(hardware, "psutil", None)
    info = hardware.get_cpu_info()
    assert isinstance(info, dict)
    assert "processor" in info
    assert "physical_cores" in info
    assert "logical_cores" in info
    assert "total_ram_bytes" in info
    # processor may be None or a string depending on platform
    assert info["processor"] is None or isinstance(info["processor"], str)


def test_get_system_info_with_no_gpus_and_shutil(monkeypatch):
    """Ensure get_system_info works when there are no GPUs and psutil is missing by using shutil.disk_usage."""
    monkeypatch.setattr(hardware, "get_gpu_info", lambda: [])
    monkeypatch.setattr(hardware, "psutil", None)

    class DU:
        total = 123456789
        used = 11111111
        free = 112345678

    # Replace the disk_usage function used inside the hardware module
    monkeypatch.setattr(hardware.shutil, "disk_usage", lambda path: DU())

    summary = hardware.get_system_info()
    assert isinstance(summary, dict)
    assert "gpus" in summary and isinstance(summary["gpus"], list)
    assert summary["gpus"] == []
    assert "cpu" in summary
    assert "disk_total_bytes" in summary
    assert summary["disk_total_bytes"] == DU.total
    assert summary["disk_free_bytes"] == DU.free


def test_try_nvidia_smi_parsing(monkeypatch):
    """Mock subprocess.check_output to return a sample nvidia-smi CSV and ensure parsing is correct."""
    sample = "0, NVIDIA Test GPU, 16384, 8192, 8192, 515.65, GPU-UUID\n"

    def fake_check_output(cmd, encoding, errors):
        assert "--query-gpu=" in " ".join(cmd)
        return sample

    monkeypatch.setattr(hardware.subprocess, "check_output", fake_check_output)

    gpus = hardware._try_nvidia_smi()
    assert isinstance(gpus, list)
    assert len(gpus) == 1
    g = gpus[0]
    assert g.index == 0
    assert "NVIDIA Test GPU" in g.name
    # total was provided as 16384 (MB) so bytes should be 16384 * 1024 * 1024
    assert g.total_vram_bytes == 16384 * 1024 * 1024
    assert g.used_vram_bytes == 8192 * 1024 * 1024
    assert g.free_vram_bytes == 8192 * 1024 * 1024
    assert g.cuda_driver_version == "515.65"
    assert g.uuid == "GPU-UUID"


def test_pretty_print_hardware_outputs_expected_sections(monkeypatch):
    fake = {
        "gpus": [
            {
                "name": "GPU1",
                "total_vram_bytes": 17179869184,
                "used_vram_bytes": 8589934592,
                "cuda_driver_version": "515.65",
                "uuid": "UUID1",
            }
        ],
        "cpu": {
            "processor": "x86_64",
            "physical_cores": "4",
            "logical_cores": "8",
            "total_ram_bytes": "34359738368",
        },
        "disk_total_bytes": 100000,
        "disk_free_bytes": 50000,
    }

    monkeypatch.setattr(hardware, "get_system_info", lambda: fake)
    out = hardware.pretty_print_hardware()
    assert "GPUs detected" in out
    assert "CPU:" in out
    assert "Disk:" in out
    assert "GPU1" in out
