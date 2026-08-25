"""External data integration layer.

Each external source (weather, soil moisture, terrain/DEM, satellite, historical
landslides) is implemented as an :class:`ExternalDataProvider`. Providers talk to
their upstream API, apply timeout/error handling, and return a *normalized*
payload. Services then persist that payload to Neon and shape it into the API
response — so every source plugs into the same ingestion pipeline:

    provider (fetch + normalize) -> service (cache/persist) -> repository -> DB
"""
