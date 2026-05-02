"""FastAPI dependency injection — database session and services."""

from __future__ import annotations

from typing import AsyncGenerator

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import async_session_factory
from app.services.trading import TradingService


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


async def get_trading_service(
    db: AsyncSession = Depends(get_db),
) -> TradingService:
    return TradingService(db)
