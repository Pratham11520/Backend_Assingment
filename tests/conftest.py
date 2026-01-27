"""Pytest configuration and fixtures."""
import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.models import Base, get_db


# Create a shared in-memory database for tests
# Using StaticPool and check_same_thread=False ensures all test sessions
# use the same in-memory database
TEST_DATABASE_URL = "sqlite+aiosqlite:///test.db"

test_engine = create_async_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False, "uri": True},
    poolclass=StaticPool,
    echo=False
)

TestSessionLocal = async_sessionmaker(
    test_engine,
    class_=AsyncSession,
    expire_on_commit=False
)


@pytest_asyncio.fixture(scope="session", autouse=True)
async def init_test_db():
    """Initialize test database schema once for all tests."""
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    # Cleanup
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture(autouse=True)
async def clean_tables():
    """Clean all tables before each test."""
    async with TestSessionLocal() as session:
        # Delete all messages
        from sqlalchemy import text
        await session.execute(text("DELETE FROM messages"))
        await session.commit()
    yield


@pytest_asyncio.fixture
async def client():
    """Create test client with database override."""
    async def get_test_db():
        async with TestSessionLocal() as session:
            yield session
    
    app.dependency_overrides[get_db] = get_test_db
    
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test"
    ) as test_client:
        yield test_client
    
    app.dependency_overrides.clear()
