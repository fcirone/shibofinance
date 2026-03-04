"""Shared pytest fixtures for API integration tests."""
import os

import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool

DATABASE_URL = os.environ.get(
    "DATABASE_URL", "postgresql+asyncpg://finance:finance@db:5432/finance"
)

_engine = create_async_engine(DATABASE_URL, echo=False, poolclass=NullPool)
_AsyncSession = sessionmaker(_engine, class_=AsyncSession, expire_on_commit=False)


@pytest_asyncio.fixture
async def db_session():
    """Provide a transactional session that rolls back after each test.

    NullPool ensures a fresh TCP connection per test, avoiding asyncpg's
    'another operation in progress' error when nesting transactions.
    """
    async with _engine.connect() as conn:
        await conn.begin()
        session = AsyncSession(
            bind=conn,
            expire_on_commit=False,
            join_transaction_mode="create_savepoint",
        )
        try:
            yield session
        finally:
            await session.close()
            await conn.rollback()
