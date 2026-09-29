"""
SQLAlchemy async engine and session factory.

Usage:
    from app.database import get_db

    async def my_route(db: AsyncSession = Depends(get_db)):
        ...
"""
from __future__ import annotations

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

import re

from app.config import settings

# asyncpg does not accept 'sslmode' as a URL query parameter.
# Strip it and pass ssl="require" via connect_args when the original URL requires SSL.
_raw_url = settings.database_url
_needs_ssl = "sslmode=require" in _raw_url
_clean_url = re.sub(r"[&?]sslmode=[^&]*", "", _raw_url)
_clean_url = re.sub(r"[&?]channel_binding=[^&]*", "", _clean_url)

_connect_args: dict = {}
if _needs_ssl:
    import ssl as _ssl
    _ssl_ctx = _ssl.create_default_context()
    _ssl_ctx.check_hostname = False
    _ssl_ctx.verify_mode = _ssl.CERT_NONE
    _connect_args["ssl"] = _ssl_ctx

engine = create_async_engine(
    _clean_url,
    echo=(settings.app_env == "development"),
    pool_pre_ping=True,
    connect_args=_connect_args,
)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    expire_on_commit=False,
    class_=AsyncSession,
)


class Base(DeclarativeBase):
    """Base class for all ORM models."""


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency that yields a database session."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
