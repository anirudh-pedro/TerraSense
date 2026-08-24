"""Service layer: business logic and the (currently mocked) data source.

Routes depend on these services, not on the data source directly, so the mock
data can be swapped for PostgreSQL/ML output without changing the API.
"""
