from __future__ import annotations

import logging
import os
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

ROOT = Path(__file__).resolve().parents[2]
load_dotenv(ROOT / ".env", override=False)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Lazy-initialised singletons — avoids crashing at import time when the
# database is temporarily unavailable.
# ---------------------------------------------------------------------------
_engine = None
_SessionLocal = None


def _build_database_url() -> str:
    """Build a database URL from environment variables.

    Priority:
      1. DATABASE_URL env var (exact string)
      2. Individual POSTGRES_* env vars
      3. SQLite fallback for local / offline development
    """
    database_url = os.getenv("DATABASE_URL")
    if database_url:
        return database_url.strip()

    postgres_user = os.getenv("POSTGRES_USER")
    postgres_password = os.getenv("POSTGRES_PASSWORD")
    postgres_host = os.getenv("POSTGRES_HOST")
    postgres_port = os.getenv("POSTGRES_PORT", "5432")
    postgres_db = os.getenv("POSTGRES_DB")

    if all([postgres_user, postgres_password, postgres_host, postgres_db]):
        return (
            f"postgresql+psycopg://{postgres_user}:{postgres_password}@"
            f"{postgres_host}:{postgres_port}/{postgres_db}"
        )

    # Fallback to SQLite so the app can start without PostgreSQL
    db_dir = ROOT / "backend" / "database"
    db_dir.mkdir(parents=True, exist_ok=True)
    sqlite_path = db_dir / "road_accident.db"
    logger.warning(
        "No PostgreSQL configuration found. Falling back to SQLite at %s",
        sqlite_path,
    )
    return f"sqlite:///{sqlite_path}"


def _get_engine():
    """Return the lazily-created SQLAlchemy engine."""
    global _engine
    if _engine is None:
        url = _build_database_url()
        connect_args = {}
        if url.startswith("sqlite"):
            connect_args["check_same_thread"] = False

        _engine = create_engine(
            url,
            future=True,
            pool_pre_ping=True,
            connect_args=connect_args,
        )
        logger.info("Database engine created for %s", url.split("@")[-1] if "@" in url else url)
    return _engine


def _get_session_factory():
    """Return the lazily-created session factory."""
    global _SessionLocal
    if _SessionLocal is None:
        _SessionLocal = sessionmaker(
            bind=_get_engine(),
            autoflush=False,
            autocommit=False,
            expire_on_commit=False,
        )
    return _SessionLocal


# Public accessor — use this in service code instead of the old `SessionLocal`.
def SessionLocal():
    """Create a new database session."""
    factory = _get_session_factory()
    return factory()


def init_db() -> None:
    """Create all tables if they do not already exist."""
    from backend.database.models import Base

    try:
        engine = _get_engine()
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables verified / created successfully.")
    except Exception:
        logger.exception(
            "Failed to initialise database tables. "
            "The application will still start; DB writes may fail."
        )
