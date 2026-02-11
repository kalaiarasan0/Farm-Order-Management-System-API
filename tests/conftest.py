import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from app.main import app
from app.db.base import Base
from app.db.database import get_async_db, async_engine as engine


@pytest.fixture
async def client():
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        yield ac


@pytest.fixture
async def session():
    async with engine.connect() as connection:
        transaction = await connection.begin()
        session_maker = async_sessionmaker(bind=connection, expire_on_commit=False)
        session = session_maker()

        # Override dependency
        app.dependency_overrides[get_async_db] = lambda: session

        yield session

        await session.close()
        await transaction.rollback()

    app.dependency_overrides.clear()
