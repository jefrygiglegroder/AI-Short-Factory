"""Configuration management for AI Short Factory (Phase 1).

Responsibilities:
- Provide a Config dataclass with sensible defaults suitable for Windows-first, local-first usage.
- Load configuration from (in order): explicit YAML/JSON config file if provided, environment variable overrides, and defaults.
- Offer a get_config() accessor that caches the loaded config for the process lifetime.
- Provide write_example_config(path) to create a template config file.

Design goals:
- Keep dependencies optional: try PyYAML if available; fall back to JSON parsing; never crash if yaml isn't installed.
- Use platform-appropriate default paths (LOCALAPPDATA on Windows, XDG/~/ on others).
- Keep the implementation small, testable, and robust.

NOTE: This is Phase 1 infrastructure — later components (logging, DB) will read settings from this module.
"""
from __future__ import annotations

import dataclasses
import json
import os
from pathlib import Path
from typing import Any, Dict, Optional


ENV_PREFIX = "AI_SHORT_FACTORY_"


@dataclasses.dataclass
class Config:
    # Directories
    storage_dir: str
    logs_dir: str
    cache_dir: str

    # Database
    db_path: str

    # Logging
    log_level: str = "INFO"

    # GPU settings
    max_vram_fraction: float = 0.9  # use up to 90% of VRAM by default

    # Model defaults (placeholders for future phases)
    model_defaults: Dict[str, Any] = dataclasses.field(default_factory=lambda: {
        "llm": {"provider": "local", "model": None},
        "tts": {"provider": "local", "voice": None},
    })

    # Other app settings
    auto_approve: bool = False


_CONFIG_CACHE: Optional[Config] = None


def _default_base_dir() -> Path:
    """Return a sensible base directory for app data (Windows-first).

    Windows: %LOCALAPPDATA%\AIShortFactory
    Other: ~/.ai_short_factory
    """
    if os.name == "nt":
        local_app = os.getenv("LOCALAPPDATA") or os.getenv("APPDATA")
        if local_app:
            return Path(local_app) / "AIShortFactory"
    # fallback to home dir
    return Path.home() / ".ai_short_factory"


def _defaults() -> Config:
    base = _default_base_dir()
    storage = base / "storage"
    logs = base / "logs"
    cache = base / "cache"
    db = base / "ai_short_factory.db"
    return Config(
        storage_dir=str(storage),
        logs_dir=str(logs),
        cache_dir=str(cache),
        db_path=str(db),
        log_level=os.getenv(f"{ENV_PREFIX}LOG_LEVEL", "INFO"),
    )


def _load_from_file(path: Path) -> Dict[str, Any]:
    """Load configuration mapping from YAML or JSON file.

    Returns a dict of configuration values. Never raises on missing optional yaml module.
    """
    data: Dict[str, Any] = {}
    if not path.exists():
        return data

    text = path.read_text(encoding="utf-8")
    # Try YAML if available
    try:
        import yaml  # type: ignore

        parsed = yaml.safe_load(text)
        if isinstance(parsed, dict):
            data = parsed
    except Exception:
        # Fall back to JSON
        try:
            parsed = json.loads(text)
            if isinstance(parsed, dict):
                data = parsed
        except Exception:
            # Malformed or unsupported format
            data = {}
    return data


def _apply_env_overrides(cfg: Config) -> Config:
    """Apply environment variable overrides to a Config object.

    Supported overrides (example env var names):
      AI_SHORT_FACTORY_STORAGE_DIR
      AI_SHORT_FACTORY_DB_PATH
      AI_SHORT_FACTORY_LOG_LEVEL
      AI_SHORT_FACTORY_MAX_VRAM_FRACTION
    """
    storage = os.getenv(f"{ENV_PREFIX}STORAGE_DIR")
    if storage:
        cfg.storage_dir = storage
    logs = os.getenv(f"{ENV_PREFIX}LOGS_DIR")
    if logs:
        cfg.logs_dir = logs
    cache = os.getenv(f"{ENV_PREFIX}CACHE_DIR")
    if cache:
        cfg.cache_dir = cache
    db = os.getenv(f"{ENV_PREFIX}DB_PATH")
    if db:
        cfg.db_path = db
    lvl = os.getenv(f"{ENV_PREFIX}LOG_LEVEL")
    if lvl:
        cfg.log_level = lvl
    mv = os.getenv(f"{ENV_PREFIX}MAX_VRAM_FRACTION")
    if mv:
        try:
            cfg.max_vram_fraction = float(mv)
        except Exception:
            pass
    aa = os.getenv(f"{ENV_PREFIX}AUTO_APPROVE")
    if aa is not None:
        cfg.auto_approve = aa.lower() in ("1", "true", "yes", "on")
    return cfg


def _merge_mapping_into_config(cfg: Config, mapping: Dict[str, Any]) -> Config:
    """Merge a mapping (from file) into the Config dataclass.

    This is intentionally shallow — file values override defaults when keys match dataclass fields.
    """
    for key, value in mapping.items():
        if not hasattr(cfg, key):
            continue
        try:
            setattr(cfg, key, value)
        except Exception:
            # ignore values that cannot be applied
            continue
    return cfg


def load_config(path: Optional[str] = None) -> Config:
    """Load configuration and return a Config instance.

    Order:
    1. Start with defaults
    2. If path provided and exists, merge values from that file
    3. Apply environment variable overrides
    """
    cfg = _defaults()
    if path:
        p = Path(path)
        if p.exists():
            mapping = _load_from_file(p)
            cfg = _merge_mapping_into_config(cfg, mapping)
    else:
        # check conventional locations: current directory config.yaml, then base dir
        candidates = [Path("config.yaml"), Path("config.yml"), Path("config.json")]
        for c in candidates:
            if c.exists():
                mapping = _load_from_file(c)
                cfg = _merge_mapping_into_config(cfg, mapping)
                break
        else:
            # also look in base dir
            base_cfg = Path(_default_base_dir()) / "config.yaml"
            if base_cfg.exists():
                mapping = _load_from_file(base_cfg)
                cfg = _merge_mapping_into_config(cfg, mapping)

    cfg = _apply_env_overrides(cfg)
    return cfg


def get_config(path: Optional[str] = None) -> Config:
    """Return a cached Config instance for the process.

    If a path is provided, it will be used only the first time to populate the cache.
    Subsequent calls ignore the path and return the cached object.
    """
    global _CONFIG_CACHE
    if _CONFIG_CACHE is None:
        _CONFIG_CACHE = load_config(path)
    return _CONFIG_CACHE


def write_example_config(path: Optional[str] = None) -> Path:
    """Write an example config.yaml to path (or default base dir) and return the path used.

    This helps users get started with a local configuration file.
    """
    if path:
        p = Path(path)
    else:
        p = Path(_default_base_dir()) / "config.yaml"
    p.parent.mkdir(parents=True, exist_ok=True)
    example = {
        "storage_dir": str(Path(p).parent / "storage"),
        "logs_dir": str(Path(p).parent / "logs"),
        "cache_dir": str(Path(p).parent / "cache"),
        "db_path": str(Path(p).parent / "ai_short_factory.db"),
        "log_level": "INFO",
        "max_vram_fraction": 0.9,
        "auto_approve": False,
    }
    # Prefer YAML if available, otherwise write JSON
    try:
        import yaml  # type: ignore

        with p.open("w", encoding="utf-8") as fh:
            yaml.safe_dump(example, fh)
    except Exception:
        with p.open("w", encoding="utf-8") as fh:
            json.dump(example, fh, indent=2)
    return p


# Expose module-level convenience
__all__ = [
    "Config",
    "load_config",
    "get_config",
    "write_example_config",
]
