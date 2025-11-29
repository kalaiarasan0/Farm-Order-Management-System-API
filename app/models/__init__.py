"""Models package.

Expose `Base` for migrations and import concrete table modules here so they
are registered on `Base.metadata`.
"""
from sqlalchemy.orm import declarative_base

# Declarative base used by all models and by Alembic migrations
Base = declarative_base()

# Import models so they register on Base.metadata
from . import tables  # noqa: F401

__all__ = ["Base"]
