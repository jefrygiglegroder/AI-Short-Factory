"""Central logging configuration for AI Short Factory.

Provides a simple, testable logging setup using the app core config.

Public API:
- configure_logging(force: bool = False, logs_dir: Optional[str] = None, level: Optional[str] = None)
- get_logger(name: str) -> logging.Logger
- reset_logging() -> None  # test helper to remove handlers and allow reconfiguration

Design:
- Config is read lazily from app.core.config.get_config().
- Uses RotatingFileHandler to keep logs manageable.
- Keeps dependencies minimal (built-in logging only).
"""
from __future__ import annotations

import logging
import logging.handlers
import os
from pathlib import Path
from typing import Optional

from app.core import config as _config_module


_CONFIGURED = False


def configure_logging(
    force: bool = False,
    *,
    logs_dir: Optional[str] = None,
    level: Optional[str] = None,
    max_bytes: int = 5 * 1024 * 1024,
    backup_count: int = 5,
) -> None:
    """Configure root logging for the application.

    If force is True, existing handlers will be removed and reconfigured.
    Optional overrides allow tests to set a temporary logs directory.
    """
    global _CONFIGURED
    if _CONFIGURED and not force:
        return

    # Remove existing handlers if forcing reconfigure
    root_logger = logging.getLogger()
    if force:
        for h in list(root_logger.handlers):
            try:
                root_logger.removeHandler(h)
                h.close()
            except Exception:
                pass

    cfg = _config_module.get_config()

    logs_path = Path(logs_dir) if logs_dir else Path(cfg.logs_dir)
    try:
        logs_path.mkdir(parents=True, exist_ok=True)
    except Exception:
        # best-effort: fall back to current directory
        logs_path = Path(".")

    level_name = (level or cfg.log_level or "INFO").upper()
    try:
        log_level = getattr(logging, level_name)
    except Exception:
        log_level = logging.INFO

    # Console handler
    ch = logging.StreamHandler()
    ch.setLevel(log_level)
    ch.setFormatter(logging.Formatter("%(asctime)s %(levelname)s [%(name)s] %(message)s", datefmt="%Y-%m-%d %H:%M:%S"))

    # File handler (rotating)
    log_file = logs_path / "application.log"
    try:
        fh = logging.handlers.RotatingFileHandler(str(log_file), maxBytes=max_bytes, backupCount=backup_count, encoding="utf-8")
        fh.setLevel(log_level)
        fh.setFormatter(logging.Formatter("%(asctime)s %(levelname)s [%(name)s] %(message)s", datefmt="%Y-%m-%d %H:%M:%S"))
    except Exception:
        fh = None

    root_logger.setLevel(log_level)
    root_logger.addHandler(ch)
    if fh:
        root_logger.addHandler(fh)

    # Avoid noisy external libraries by setting default levels (can be overridden by config later)
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("botocore").setLevel(logging.WARNING)

    _CONFIGURED = True


def get_logger(name: str) -> logging.Logger:
    """Return a logger with the application configuration applied.

    Ensures configure_logging() has been called once.
    """
    if not _CONFIGURED:
        configure_logging()
    return logging.getLogger(name)


def reset_logging() -> None:
    """Test helper: remove all handlers from the root logger and mark as unconfigured.

    Use in unit tests to ensure isolation between tests that change logging configuration.
    """
    global _CONFIGURED
    root_logger = logging.getLogger()
    for h in list(root_logger.handlers):
        try:
            root_logger.removeHandler(h)
            h.close()
        except Exception:
            pass
    _CONFIGURED = False


__all__ = ["configure_logging", "get_logger", "reset_logging"]
