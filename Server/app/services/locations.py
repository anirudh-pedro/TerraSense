"""District/location resolution.

Maps a requested name (district, state, or common city) to a canonical NER
district, its coordinates, and — when the database is available — its
``district_id`` for foreign-key persistence.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Optional

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.models import District

logger = logging.getLogger(__name__)

# Canonical district catalog: key (lowercase) -> (name, state, lat, lng).
_CATALOG: dict[str, tuple[str, str, float, float]] = {
    "aizawl": ("Aizawl", "Mizoram", 23.7271, 92.7176),
    "champhai": ("Champhai", "Mizoram", 23.4739, 93.3295),
    "kohima": ("Kohima", "Nagaland", 25.6751, 94.1086),
    "east khasi hills": ("East Khasi Hills", "Meghalaya", 25.5788, 91.8933),
    "papum pare": ("Papum Pare", "Arunachal Pradesh", 27.0844, 93.6053),
    "gangtok": ("Gangtok", "Sikkim", 27.3389, 88.6065),
    "imphal east": ("Imphal East", "Manipur", 24.8170, 93.9368),
    "kamrup metro": ("Kamrup Metro", "Assam", 26.1445, 91.7362),
    "west tripura": ("West Tripura", "Tripura", 23.8315, 91.2868),
}

# Common city / state aliases -> canonical catalog key.
_ALIASES: dict[str, str] = {
    # cities
    "shillong": "east khasi hills",
    "itanagar": "papum pare",
    "imphal": "imphal east",
    "guwahati": "kamrup metro",
    "agartala": "west tripura",
    # states -> representative district
    "mizoram": "aizawl",
    "nagaland": "kohima",
    "meghalaya": "east khasi hills",
    "arunachal pradesh": "papum pare",
    "sikkim": "gangtok",
    "manipur": "imphal east",
    "assam": "kamrup metro",
    "tripura": "west tripura",
}


@dataclass
class ResolvedLocation:
    """A resolved district with coordinates and (optional) DB id."""

    name: str
    state: str
    latitude: float
    longitude: float
    district_id: Optional[int] = None


def resolve_location(db: Optional[Session], district: Optional[str]) -> ResolvedLocation:
    """Resolve a requested name to a canonical district + coordinates + DB id."""
    settings = get_settings()
    requested = (district or settings.weather_default_district).strip()
    key = requested.lower()

    if key in ("", "all ner states"):
        key = settings.weather_default_district.lower()
    key = _ALIASES.get(key, key)

    if key not in _CATALOG:
        logger.info("Unknown location '%s'; falling back to default district.", requested)
        key = settings.weather_default_district.lower()

    name, state, lat, lng = _CATALOG[key]

    district_id: Optional[int] = None
    if db is not None:
        try:
            district_id = db.execute(
                select(District.id).where(func.lower(District.name) == name.lower())
            ).scalar_one_or_none()
        except Exception:  # pragma: no cover - DB optional/degraded
            logger.warning("District lookup failed for %s; continuing without persistence.", name)

    return ResolvedLocation(name=name, state=state, latitude=lat, longitude=lng, district_id=district_id)
