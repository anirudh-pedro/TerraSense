"""Repositories: the only layer that reads/writes ORM models for a resource.

Services depend on repositories rather than issuing queries directly, which
keeps persistence concerns isolated and reusable across data sources.
"""
