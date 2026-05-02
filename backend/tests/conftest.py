"""Pytest fixtures for tests."""

from __future__ import annotations

import asyncio
import uuid
from decimal import Decimal

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.database import Base


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="function")
async def db_session():
    """Create a fresh database session with in-memory SQLite for testing."""
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        echo=False,
    )

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )

    async with session_factory() as session:
        yield session
        await session.rollback()

    await engine.dispose()


@pytest.fixture
def account_id() -> uuid.UUID:
    return uuid.uuid4()


@pytest.fixture
def sample_account_data():
    return {
        "name": "test-account",
        "account_type": "simulated",
        "quote_asset": "USDT",
        "initial_balance": Decimal("10000"),
    }
