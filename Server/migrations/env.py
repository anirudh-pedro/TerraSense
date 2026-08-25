"""Alembic migration environment for TerraSense NER.

- Pulls the database URL from application settings (DATABASE_URL in .env).
- Registers all ORM metadata so `--autogenerate` works.
- Imports geoalchemy2 so geometry types render correctly in migrations.
- Skips PostGIS-managed tables (spatial_ref_sys, etc.) during autogenerate.
"""

import sys
from logging.config import fileConfig
from pathlib import Path

from alembic import context
from sqlalchemy import engine_from_config, pool

# Make the Server/ package importable when Alembic runs from that directory.
sys.path.append(str(Path(__file__).resolve().parents[1]))

import geoalchemy2  # noqa: F401  (ensures geometry types are registered)

from app.core.config import get_settings  # noqa: E402
from app.db.base import Base  # noqa: E402
import app.db.models  # noqa: E402,F401  (registers all tables on Base.metadata)

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Inject the runtime database URL from settings.
_settings = get_settings()
_db_url = _settings.database_url or config.get_main_option("sqlalchemy.url") or ""
config.set_main_option("sqlalchemy.url", _db_url)

target_metadata = Base.metadata

# PostGIS creates/manages these; never emit migrations for them.
_POSTGIS_TABLES = {"spatial_ref_sys", "geometry_columns", "geography_columns", "raster_columns", "raster_overviews"}


def include_object(obj, name, type_, reflected, compare_to):  # noqa: ANN001
    if type_ == "table" and name in _POSTGIS_TABLES:
        return False
    # GeoAlchemy2 manages spatial indexes itself; don't let autogenerate touch them.
    if type_ == "index" and name and str(name).startswith("idx_") and "geom" in str(name):
        return False
    return True


def run_migrations_offline() -> None:
    """Emit SQL without a live DB connection (`alembic ... --sql`)."""
    context.configure(
        url=_db_url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        include_object=include_object,
        compare_type=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations against a live database connection."""
    section = config.get_section(config.config_ini_section) or {}
    section["sqlalchemy.url"] = _db_url
    connectable = engine_from_config(section, prefix="sqlalchemy.", poolclass=pool.NullPool)
    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            include_object=include_object,
            compare_type=True,
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
