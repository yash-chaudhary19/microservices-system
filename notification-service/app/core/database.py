import logging
from collections.abc import AsyncGenerator
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase
from app.core.config import settings

logger = logging.getLogger("notification_service.database")


class Base(DeclarativeBase):
    """Declarative base class for Notification models."""
    pass


def get_async_database_url(url: str) -> str:
    """Ensure database URL uses asyncpg driver for SQLAlchemy async engine."""
    if url.startswith("postgresql+psycopg2://"):
        return url.replace("postgresql+psycopg2://", "postgresql+asyncpg://", 1)
    if url.startswith("postgresql://"):
        return url.replace("postgresql://", "postgresql+asyncpg://", 1)
    if url.startswith("postgres://"):
        return url.replace("postgres://", "postgresql+asyncpg://", 1)
    return url


db_url = get_async_database_url(settings.DATABASE_URL)

engine = create_async_engine(
    db_url,
    echo=(settings.LOG_LEVEL.upper() == "DEBUG"),
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
)

async_session_factory = async_sessionmaker(
    bind=engine,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency for obtaining an async session."""
    async with async_session_factory() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise


async def init_db() -> None:
    """Initialize database tables for notifications."""
    async with engine.begin() as conn:
        logger.info("Initializing Notification Service database schema...")
        await conn.run_sync(Base.metadata.create_all)
        logger.info("Notification Service database schema initialized successfully.")
