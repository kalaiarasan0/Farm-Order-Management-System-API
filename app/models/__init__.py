"""Models package.

Expose `Base` for migrations and import concrete table modules here so they
are registered on `Base.metadata`.
"""

from app.db import Base, TrackingBase

# Import models so they register on Base.metadata
from . import tables  # noqa: F401

# Import tracking models so they register on TrackingBase.metadata
from . import tracking_tables  # noqa: F401


__all__ = ["Base", "TrackingBase"]
