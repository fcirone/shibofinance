"""Shared pytest fixtures for API integration tests."""
import os
import uuid

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool

DATABASE_URL = os.environ.get(
    "DATABASE_URL", "postgresql+asyncpg://finance:finance@db:5432/finance"
)

_engine = create_async_engine(DATABASE_URL, echo=False, poolclass=NullPool)
_AsyncSession = sessionmaker(_engine, class_=AsyncSession, expire_on_commit=False)


@pytest.fixture(autouse=True)
def restore_importer_registry():
    """Restore the importer registry after each test.

    test_importer_framework.py clears the registry for isolation; this fixture
    ensures all other tests still see the real importers.
    """
    from importers import registry
    saved = registry._registry[:]
    yield
    registry._registry[:] = saved


@pytest_asyncio.fixture
async def client(db_session):
    """AsyncClient wired to the FastAPI app with a test DB session."""
    from app.db import get_db
    from app.main import app

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c
    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def instrument(db_session):
    """A minimal bank account instrument for use in tests."""
    from app.models import ImportStatus, Instrument, InstrumentSource, InstrumentType

    inst = Instrument(
        id=uuid.uuid4(),
        name="Test Bank",
        type=InstrumentType.bank_account,
        source=InstrumentSource.santander_br,
        currency="BRL",
        source_instrument_id=str(uuid.uuid4()),
    )
    db_session.add(inst)
    await db_session.flush()
    return inst


@pytest_asyncio.fixture
async def batch(db_session, instrument):
    """A minimal import batch for use in tests."""
    from app.models import ImportBatch, ImportStatus

    b = ImportBatch(
        id=uuid.uuid4(),
        instrument_id=instrument.id,
        filename="test.csv",
        sha256="b" * 64,
        status=ImportStatus.processed,
    )
    db_session.add(b)
    await db_session.flush()
    return b


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
