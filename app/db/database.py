from typing import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.config import settings
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from app.db.base import Base, UserBase, AsyncBase


# Create a synchronous SQLAlchemy engine using the project's DATABASE_URL.

engine = create_engine(
    settings.DATABASE_URL, pool_pre_ping=True, future=True
    )
async_engine = create_async_engine(
    settings.ASYNC_DATABASE_URL,pool_size=10, max_overflow=20, pool_recycle = 3600, pool_pre_ping=True, future=True
)
user_engine = create_engine(
    settings.USER_DATABASE_URL, pool_pre_ping=True, future=True
    )
async_user_engine = create_async_engine(
    settings.ASYNC_USER_DATABASE_URL,pool_size=10, max_overflow=20, pool_recycle = 3600, pool_pre_ping=True, future=True
)
SessionLocal = sessionmaker(
    bind=engine, autoflush=True, autocommit=False
    )
AsyncSessionLocal = async_sessionmaker(
    bind=async_engine, autoflush=True, autocommit=False, class_=AsyncSession,
    expire_on_commit=False
)
UserSessionLocal = sessionmaker(
    bind=user_engine, autoflush=True, autocommit=False
)
AsyncUserSessionLocal = async_sessionmaker(
    bind=async_user_engine, autoflush=True, autocommit=False, class_=AsyncSession,
    expire_on_commit=False
)

def get_db() -> Generator:
    """FastAPI dependency that yields a database session and closes it."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

async def get_async_db() -> AsyncSession:
    async with AsyncSessionLocal() as db:
        try:
            yield db
        finally:
            await db.close()

def get_user_db() -> Generator:
    db = UserSessionLocal()
    try:
        yield db
    finally:
        db.close()

async def get_async_user_db() -> AsyncSession:
    async with AsyncUserSessionLocal() as db:
        try:
            yield db
        finally:
            await db.close()

def init_db() -> None:
    """Create database tables from models metadata.

    This will create tables using the engine and the metadata exposed by models' Base.
    Use this for local development only; prefer Alembic for migrations in production.
    """
    from app.models import tracking_tables  # noqa: F401
    from app.models import user_tables  # noqa: F401
    
    Base.metadata.create_all(bind=engine)
    AsyncBase.metadata.create_all(bind=async_engine)
    UserBase.metadata.create_all(bind=user_engine)
