import asyncpg
import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy import delete
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from unittest.mock import AsyncMock

from src.library_catalog.main import app
from src.library_catalog.core.database import Base, get_db
from src.library_catalog.api.dependencies import get_openlibrary_client
from src.library_catalog.data.models.book import Book

TEST_DB_URL = "postgresql+asyncpg://postgres:postgres@localhost:5432/library_test"
TEST_DB_ADMIN_URL = "postgresql://postgres:postgres@localhost:5432/postgres"


async def _ensure_test_db_exists() -> None:
    """Создать тестовую БД если она не существует."""
    conn = await asyncpg.connect(TEST_DB_ADMIN_URL)
    try:
        exists = await conn.fetchval(
            "SELECT 1 FROM pg_database WHERE datname = 'library_test'"
        )
        if not exists:
            await conn.execute("CREATE DATABASE library_test")
    finally:
        await conn.close()


@pytest_asyncio.fixture(scope="session")
async def engine():
    await _ensure_test_db_exists()
    _engine = create_async_engine(TEST_DB_URL)
    async with _engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield _engine
    async with _engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await _engine.dispose()


@pytest_asyncio.fixture
async def db_session(engine):
    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    async with session_factory() as session:
        yield session
        await session.rollback()


@pytest.fixture
def mock_ol_client():
    """Мок OpenLibraryClient — не делает реальных HTTP-запросов."""
    client = AsyncMock()
    client.enrich = AsyncMock(return_value={})
    return client


@pytest_asyncio.fixture
async def client(db_session: AsyncSession, mock_ol_client):
    """
    HTTP-клиент для интеграционных тестов.

    - Переопределяет get_db на тестовую сессию с commit после каждого запроса
    - Мокает OpenLibraryClient чтобы не делать реальных HTTP-запросов
    - Очищает таблицу books после каждого теста
    """
    async def override_get_db():
        try:
            yield db_session
            await db_session.commit()
        except Exception:
            await db_session.rollback()
            raise

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_openlibrary_client] = lambda: mock_ol_client

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c

    app.dependency_overrides.clear()
    await db_session.execute(delete(Book))
    await db_session.commit()
