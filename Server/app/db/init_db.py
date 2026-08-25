"""Quick database bootstrap for development.

Enables PostGIS and creates all tables directly from the ORM metadata. This is
a convenience for local/dev use; production deployments should use Alembic
(`alembic upgrade head`) as the source of truth.

Usage:
    python -m app.db.init_db
"""

import logging

from sqlalchemy import text

from app.core.logging import configure_logging
from app.db.base import Base
from app.db.session import get_engine
import app.db.models  # noqa: F401  (registers tables on Base.metadata)

logger = logging.getLogger("terrasense.init_db")


def init_db() -> None:
    engine = get_engine()
    with engine.begin() as conn:
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS postgis"))
    Base.metadata.create_all(bind=engine)
    logger.info("Database initialized: PostGIS enabled and %d tables ensured.", len(Base.metadata.tables))


if __name__ == "__main__":
    configure_logging()
    init_db()
