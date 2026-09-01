import os
import logging
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import declarative_base
from sqlalchemy import text
from backend.app.config import settings

logger = logging.getLogger("razorloop.database")

Base = declarative_base()

db_url = settings.DATABASE_URL
if "sqlite" in db_url:
    connect_args = {"check_same_thread": False, "timeout": 30}
else:
    if db_url.startswith("postgresql://"):
        try:
            import asyncpg
            db_url = db_url.replace("postgresql://", "postgresql+asyncpg://")
            connect_args = {}
        except ImportError:
            logger.warning("asyncpg not installed, falling back to SQLite dev.db")
            db_url = "sqlite+aiosqlite:///./dev.db"
            connect_args = {"check_same_thread": False, "timeout": 30}
    else:
        connect_args = {}

try:
    engine = create_async_engine(db_url, echo=False, connect_args=connect_args)
except Exception as e:
    logger.warning(f"Failed to initialize database engine for {db_url}: {e}. Falling back to SQLite.")
    db_url = "sqlite+aiosqlite:///./dev.db"
    engine = create_async_engine(db_url, echo=False, connect_args={"check_same_thread": False, "timeout": 30})

async_session_factory = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False
)

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_factory() as session:
        try:
            yield session
        finally:
            await session.close()

async def init_db():
    async with engine.begin() as conn:
        if "sqlite" in db_url:
            await conn.execute(text("PRAGMA journal_mode=WAL;"))
            await conn.execute(text("PRAGMA busy_timeout=5000;"))
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database tables initialized successfully with WAL mode.")
