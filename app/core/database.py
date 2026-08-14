"""Database utilities for AI Short Factory.

Provides SQLAlchemy engine creation, declarative Base, session factory, and a
convenient contextmanager for transactional sessions. Designed for SQLite in
Phase 1 but written to be extensible for other engines.

Public API:
- Base: declarative base for models
- get_engine(db_path: Optional[str] = None, echo: bool = False) -> Engine
- get_session_factory(engine: Optional[Engine] = None) -> sessionmaker
- session_scope(engine: Optional[Engine] = None): contextmanager yielding Session
- init_db(engine: Optional[Engine] = None, create_tables: bool = True)

Notes:
- Reads default db_path from app.core.config.get_config() when None.
- Applies SQLite pragmas (foreign_keys=ON, journal_mode=WAL) on connect.
- Uses check_same_thread=False to allow multithreaded access; be careful with concurrency.
"""
from __future__ import annotations

import contextlib
import importlib
import logging
from pathlib import Path
from typing import Iterator, Optional

from sqlalchemy import event, create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import declarative_base, sessionmaker, Session

from app.core.config import get_config
from app.core.logging import get_logger

logger = get_logger(__name__)

Base = declarative_base()

# Module-level default engine used by get_engine() and session helpers when no explicit
# engine is provided. Tests can call init_db(engine) to set the default engine for the
# current process so repositories/session_scope() will use the same Engine instance.
_DEFAULT_ENGINE: Optional[Engine] = None


def _create_sqlite_uri(db_path: str) -> str:
    # Ensure absolute path and proper sqlite URI
    p = Path(db_path).expanduser().resolve()
    return f"sqlite:///{p}"


def _apply_sqlite_pragmas(dbapi_connection, connection_record):
    """Apply runtime pragmas to SQLite connections for durability and foreign keys."""
    try:
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys = ON")
        # Enable WAL for better concurrency when available
        try:
            cursor.execute("PRAGMA journal_mode=WAL")
            # consume the result for some pysqlite versions
            _ = cursor.fetchone()
        except Exception:
            # journal_mode may not be supported in some environments; ignore
            pass
        cursor.close()
    except Exception as exc:  # pragma: no cover - defensive
        # Avoid failing on PRAGMA errors; just log for diagnosis
        logging.getLogger(__name__).debug("Failed to apply sqlite pragmas: %s", exc)


def get_engine(db_path: Optional[str] = None, echo: bool = False) -> Engine:
    """Create and return a SQLAlchemy Engine.

    Behavior:
    - If db_path is None and a default engine has previously been set (via init_db or
      earlier get_engine without db_path), return that default engine.
    - If db_path is None and no default engine exists, construct one from config and
      cache it as the default for subsequent calls.
    - If db_path is provided, construct and return a new Engine bound to that path
      (without changing the default engine).

    This lets tests create a temporary Engine and then call init_db(engine) to make
    it the application's default for the duration of the test.
    """
    global _DEFAULT_ENGINE
    if db_path is None:
        if _DEFAULT_ENGINE is not None:
            return _DEFAULT_ENGINE
        cfg = get_config()
        db_path = cfg.db_path

    uri = _create_sqlite_uri(db_path)
    engine = create_engine(uri, echo=echo, connect_args={"check_same_thread": False}, future=True)

    # Apply SQLite pragmas on every new DBAPI connection
    if "sqlite" in uri:
        try:
            event.listen(engine, "connect", _apply_sqlite_pragmas)
        except Exception:
            logger.debug("Could not attach sqlite pragmas event listener")

    # If caller asked for the default engine (no db_path provided originally), cache it
    if db_path is not None and _DEFAULT_ENGINE is None and get_config().db_path == str(Path(db_path).resolve()):
        # Only auto-cache when the created engine corresponds to the configured default path
        _DEFAULT_ENGINE = engine

    return engine


def get_session_factory(engine: Optional[Engine] = None):
    """Return a SQLAlchemy sessionmaker bound to the given engine (or default engine).

    The returned factory creates Session objects (context-managed by session_scope).
    """
    if engine is None:
        engine = get_engine()
    return sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)


@contextlib.contextmanager
def session_scope(engine: Optional[Engine] = None) -> Iterator[Session]:
    """Provide a transactional scope around a series of operations.

    Usage:
        with session_scope() as session:
            session.add(obj)
    Commits on success; rolls back and re-raises on exception; always closes.
    """
    factory = get_session_factory(engine)
    session: Session = factory()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def init_db(engine: Optional[Engine] = None, create_tables: bool = True) -> None:
    """Initialize the database file/directory and optionally create tables.

    Non-destructive: create_tables will call Base.metadata.create_all(engine)
    which only creates missing tables and does not drop existing ones.

    If an Engine is provided, this function will set it as the module default so
    subsequent calls to get_engine() or session_scope() without parameters will
    use the same Engine instance (this is important for tests that create an
    isolated temporary database).
    """
    global _DEFAULT_ENGINE
    if engine is None:
        engine = get_engine()

    # Ensure the directory exists for SQLite files
    try:
        url = str(engine.url)
        if url.startswith("sqlite:///"):
            # Extract path after sqlite:///
            path = Path(url.replace("sqlite:///", ""))
            if not path.exists():
                path.parent.mkdir(parents=True, exist_ok=True)
    except Exception:
        # If anything unexpected happens, continue and let SQLAlchemy handle it
        logger.debug("init_db: could not ensure db directory exists")

    # Set the module-level default engine to the provided one so repository code
    # that uses session_scope() without an explicit engine will operate against
    # the same database instance.
    _DEFAULT_ENGINE = engine

    if create_tables:
        try:
            # Ensure application models are imported and registered with Base.metadata
            try:
                importlib.import_module("app.models")
            except Exception:
                logger.debug("Could not import 'app.models' prior to create_all()", exc_info=True)

            Base.metadata.create_all(engine)
            logger.info("Database initialized and tables created (if needed)")
        except Exception as exc:
            logger.error("Error creating tables: %s", exc)
            raise


__all__ = [
    "Base",
    "get_engine",
    "get_session_factory",
    "session_scope",
    "init_db",
]
