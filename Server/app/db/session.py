"""Database engine and session management.

The engine is created lazily so importing the app never requires a live
database (e.g. the weather endpoints work without DB configured). Configure
`DATABASE_URL` in `.env` to enable persistence.
"""

import logging
from collections.abc import Iterator
from functools import lru_cache
from typing import Optional

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import get_settings

logger = logging.getLogger(__name__)


@lru_cache
def get_engine() -> Engine:
    """Create (once) and return the SQLAlchemy engine."""
    settings = get_settings()
    if not settings.database_url:
        raise RuntimeError(
            "DATABASE_URL is not configured. Set it in Server/.env to use the database."
        )
    engine = create_engine(
        settings.database_url,
        echo=settings.db_echo,
        pool_pre_ping=settings.db_pool_pre_ping,
        pool_size=settings.db_pool_size,
        max_overflow=settings.db_max_overflow,
        future=True,
    )
    logger.debug("Database engine created")
    return engine


@lru_cache
def get_sessionmaker() -> sessionmaker[Session]:
    """Return a cached session factory bound to the engine."""
    return sessionmaker(
        bind=get_engine(),
        autoflush=False,
        autocommit=False,
        expire_on_commit=False,
        future=True,
    )


def get_db() -> Iterator[Session]:
    """FastAPI dependency yielding a database session (per request)."""
    session = get_sessionmaker()()
    try:
        yield session
    finally:
        session.close()


def get_optional_db() -> Iterator[Optional[Session]]:
    """Like :func:`get_db`, but yields ``None`` when the DB is not configured
    or the engine can't be created — so endpoints can degrade gracefully
    instead of failing the whole request."""
    if not get_settings().database_url:
        yield None
        return
    try:
        session = get_sessionmaker()()
    except Exception:
        logger.warning("Database unavailable; continuing without persistence.")
        yield None
        return
    try:
        yield session
    finally:
        session.close()
