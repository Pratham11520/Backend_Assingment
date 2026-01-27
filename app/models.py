"""Database models and initialization."""
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from sqlalchemy import Column, String, Text
from datetime import datetime

from app.config import settings

Base = declarative_base()


class Message(Base):
    """SQLite message model."""
    __tablename__ = "messages"

    message_id = Column(String, primary_key=True, index=True)
    from_msisdn = Column(String, nullable=False)
    to_msisdn = Column(String, nullable=False)
    ts = Column(String, nullable=False)  # ISO-8601 UTC string
    text = Column(Text, nullable=True)
    created_at = Column(String, nullable=False)


# Create async engine
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=False,
    connect_args={"check_same_thread": False} if "sqlite" in settings.DATABASE_URL else {}
)

# Session factory
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False
)


async def init_db():
    """Initialize database schema."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def get_db():
    """Dependency for getting database session."""
    async with AsyncSessionLocal() as session:
        yield session
