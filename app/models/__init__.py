"""Models package.

Expose `Base` for migrations and import concrete table modules here so they
are registered on `Base.metadata`.
"""

from sqlalchemy.orm import declarative_base

# Declarative base used by all models and by Alembic migrations
Base = declarative_base()

# Import models so they register on Base.metadata
from . import tables  # noqa: F401

# Import tracking models so they register on TrackingBase.metadata
from . import tracking_tables  # noqa: F401
from app.db import TrackingBase

__all__ = ["Base", "TrackingBase"]
