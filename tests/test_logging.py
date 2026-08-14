import logging
from app.core import logging as app_logging


def test_configure_logging_creates_log_file(tmp_path):
    logs_dir = tmp_path / "logs"
    # Reset any global logging configuration to isolate test
    app_logging.reset_logging()
    app_logging.configure_logging(force=True, logs_dir=str(logs_dir), level="DEBUG")

    logger = app_logging.get_logger("ai_short_factory.test")
    logger.debug("unit test debug message")
    logger.info("unit test info message")

    # Ensure handlers flushed
    for h in logging.getLogger().handlers:
        try:
            h.flush()
        except Exception:
            pass

    # Check that a log file exists and contains our messages
    log_files = list(logs_dir.glob("*.log"))
    assert len(log_files) >= 1
    content = log_files[0].read_text(encoding="utf-8")
    assert "unit test info message" in content


def test_log_level_respected(tmp_path):
    logs_dir = tmp_path / "logs2"
    app_logging.reset_logging()
    app_logging.configure_logging(force=True, logs_dir=str(logs_dir), level="ERROR")

    logger = app_logging.get_logger("ai_short_factory.test2")
    logger.debug("this should not appear")
    logger.error("this is an error")

    for h in logging.getLogger().handlers:
        try:
            h.flush()
        except Exception:
            pass

    log_files = list(logs_dir.glob("*.log"))
    assert len(log_files) >= 1
    content = log_files[0].read_text(encoding="utf-8")
    assert "this is an error" in content
    assert "this should not appear" not in content
