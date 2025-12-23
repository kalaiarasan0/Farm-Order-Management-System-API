from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

from app.config import settings

# Create a synchronous SQLAlchemy engine using the project's DATABASE_URL.
# For MySQL use e.g. "mysql+pymysql://user:pass@127.0.0.1:3306/farmai?charset=utf8mb4"
engine = create_engine(settings.DATABASE_URL, pool_pre_ping=True, future=True)
tracking_engine = create_engine(
    settings.TRACKING_DATABASE_URL, pool_pre_ping=True, future=True
)

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
TrackingSessionLocal = sessionmaker(
    bind=tracking_engine, autoflush=False, autocommit=False
)


# Define TrackingBase here so it can be imported by tracking models
TrackingBase = declarative_base()


def get_db() -> Generator:
    """FastAPI dependency that yields a database session and closes it."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_tracking_db() -> Generator:
    db = TrackingSessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    """Create database tables from models metadata.

    This will create tables using the engine and the metadata exposed by models' Base.
    Use this for local development only; prefer Alembic for migrations in production.
    """
    # Import here to ensure models are registered on Base.metadata
    from app.models import Base

    # Import tracking models to ensure they are registered on TrackingBase.metadata
    from app.models import tracking_tables  # noqa: F401

    Base.metadata.create_all(bind=engine)
    TrackingBase.metadata.create_all(bind=tracking_engine)
