from __future__ import annotations

from pathlib import Path

from sqlalchemy.ext.asyncio import AsyncEngine, async_sessionmaker, create_async_engine

from netframework_core.persistence.base import Base


def create_engine(url: str, *, echo: bool = False) -> AsyncEngine:
    if url.startswith("sqlite"):
        db_path = url.split("///")[-1]
        if db_path and db_path != ":memory:":
            Path(db_path).parent.mkdir(parents=True, exist_ok=True)
    return create_async_engine(url, echo=echo, future=True)


def create_session_factory(engine: AsyncEngine) -> async_sessionmaker:
    return async_sessionmaker(engine, expire_on_commit=False)


async def create_all_tables(engine: AsyncEngine) -> None:
    """Dev/demo convenience. Swap for Alembic migrations per-service for
    anything that needs schema versioning across environments."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
