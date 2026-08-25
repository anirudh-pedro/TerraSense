"""initial schema — PostGIS extension, enums, all tables + spatial indexes

Baseline migration. It enables PostGIS and creates the full schema directly
from the ORM metadata (app.db.models), so the migration can never drift from
the models. Subsequent changes should use `alembic revision --autogenerate`.

Revision ID: 0001_initial
Revises:
Create Date: 2026-08-24
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import geoalchemy2  # noqa: F401

from app.db.base import Base
import app.db.models  # noqa: F401  (registers all tables on Base.metadata)

# revision identifiers, used by Alembic.
revision: str = "0001_initial"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# Native enum types created by this schema (dropped on downgrade).
_ENUM_TYPES = (
    "risk_status",
    "user_role",
    "incident_type",
    "incident_source",
    "incident_status",
    "road_status",
    "notification_category",
)


def upgrade() -> None:
    # PostGIS must exist before any geometry column is created.
    op.execute("CREATE EXTENSION IF NOT EXISTS postgis")

    bind = op.get_bind()
    # Create every table, enum type, FK and (GIST) index exactly as the models
    # define them. GeoAlchemy2 adds spatial indexes for geometry columns.
    Base.metadata.create_all(bind=bind)


def downgrade() -> None:
    bind = op.get_bind()
    Base.metadata.drop_all(bind=bind)
    # Drop enum types explicitly in case they linger after table drops.
    for type_name in _ENUM_TYPES:
        op.execute(f"DROP TYPE IF EXISTS {type_name}")
    # Note: the PostGIS extension is intentionally left installed.
