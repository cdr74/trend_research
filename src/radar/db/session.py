"""Database engine configuration and session management."""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from typing import Any

from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from radar.core.config import settings
from radar.db.tables import Base

_engine: AsyncEngine | None = None
_session_maker: async_sessionmaker[AsyncSession] | None = None


def get_engine(db_url: str | None = None) -> AsyncEngine:
    """Retrieve or initialize the async engine."""
    global _engine
    if _engine is None or db_url is not None:
        url = db_url or settings.database_url
        _engine = create_async_engine(
            url,
            echo=False,
            future=True,
            pool_pre_ping=True,
        )
    return _engine


def get_session_maker(engine: AsyncEngine | None = None) -> async_sessionmaker[AsyncSession]:
    """Retrieve or initialize the async session maker."""
    global _session_maker
    eng = engine or get_engine()
    if _session_maker is None or engine is not None:
        _session_maker = async_sessionmaker(
            bind=eng,
            class_=AsyncSession,
            expire_on_commit=False,
            autoflush=False,
        )
    return _session_maker


@asynccontextmanager
async def get_db_session() -> AsyncGenerator[AsyncSession, Any]:
    """Provide an asynchronous transactional database session scope."""
    sm = get_session_maker()
    async with sm() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


async def init_db(engine: AsyncEngine | None = None) -> None:
    """Initialize database schemas and extensions."""
    eng = engine or get_engine()
    async with eng.begin() as conn:
        # Enable pgvector extension
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector;"))
        # Create all tables
        await conn.run_sync(Base.metadata.create_all)


async def check_db_health(engine: AsyncEngine | None = None) -> bool:
    """Verify database connectivity."""
    try:
        eng = engine or get_engine()
        async with eng.connect() as conn:
            res = await conn.execute(text("SELECT 1"))
            return bool(res.scalar_one() == 1)
    except Exception:
        return False
