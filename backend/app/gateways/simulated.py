"""Simulated exchange gateway — local matching, no real Binance API calls."""

from __future__ import annotations

import logging
import uuid
from datetime import UTC, datetime
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.gateways.base import ExchangeGateway, LeverageResult, OrderResult
from app.models.order import Order
from app.services.matching import SimulatedMatchingEngine
from app.services.portfolio import PortfolioService

logger = logging.getLogger(__name__)


class SimulatedExchangeGateway(ExchangeGateway):
    """Handles all trading operations for simulated accounts locally.

    Does NOT call any Binance trading endpoints.
    """

    def __init__(self, session: AsyncSession):
        self._session = session
        self._engine = SimulatedMatchingEngine(session)
        self._portfolio = PortfolioService(session)

    async def set_leverage(
        self, account_id: str, symbol: str, leverage: int
    ) -> LeverageResult:
        aid = uuid.UUID(account_id)
        pos = await self._portfolio.get_or_create_position(
            aid, symbol, leverage, "BOTH"
        )
        pos.leverage = leverage
        await self._session.flush()
        logger.info(
            "Simulated leverage set account=%s symbol=%s leverage=%d",
            account_id, symbol, leverage,
        )
        return LeverageResult(
            account_id=account_id,
            symbol=symbol,
            leverage=leverage,
        )

    async def place_order(
        self,
        account_id: str,
        client_order_id: str,
        symbol: str,
        side: str,
        order_type: str,
        quantity: Decimal,
        leverage: int,
        reduce_only: bool = False,
    ) -> OrderResult:
        aid = uuid.UUID(account_id)

        # Check for duplicate client_order_id
        existing = await self._get_order_by_client_id(aid, client_order_id)
        if existing:
            return self._order_to_result(existing)

        order = await self._engine.execute_order(
            account_id=aid,
            symbol=symbol,
            side=side,
            quantity=quantity,
            leverage=leverage,
            client_order_id=client_order_id,
            reduce_only=reduce_only,
        )
        return self._order_to_result(order)

    async def close_position(
        self,
        account_id: str,
        client_order_id: str,
        symbol: str,
        quantity: Decimal,
    ) -> OrderResult:
        aid = uuid.UUID(account_id)

        # Check for duplicate
        existing = await self._get_order_by_client_id(aid, client_order_id)
        if existing:
            return self._order_to_result(existing)

        # Determine position direction and generate reverse order
        pos = await self._portfolio.get_position(aid, symbol, "BOTH")
        if pos is None or pos.quantity == 0:
            raise ValueError(f"No open position for {symbol}")

        if pos.quantity > 0:
            close_side = "SELL"
        else:
            close_side = "BUY"

        actual_qty = min(quantity, abs(pos.quantity))

        order = await self._engine.execute_order(
            account_id=aid,
            symbol=symbol,
            side=close_side,
            quantity=actual_qty,
            leverage=pos.leverage,
            client_order_id=client_order_id,
            reduce_only=True,
        )
        return self._order_to_result(order)

    async def _get_order_by_client_id(
        self, account_id: uuid.UUID, client_order_id: str
    ) -> Order | None:
        stmt = select(Order).where(
            Order.account_id == account_id,
            Order.client_order_id == client_order_id,
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    def _order_to_result(self, order: Order) -> OrderResult:
        account_type = "simulated"
        return OrderResult(
            account_id=str(order.account_id),
            account_type=account_type,
            client_order_id=order.client_order_id,
            exchange_order_id=order.exchange_order_id,
            symbol=order.symbol,
            side=order.side,
            order_type=order.type,
            status=order.status,
            executed_qty=order.executed_qty,
            avg_price=order.avg_price,
            leverage=order.requested_leverage,
            realized_pnl=Decimal("0"),  # aggregated from fills if needed
            fee_amount=Decimal("0"),  # aggregated from fills if needed
            reduce_only=order.reduce_only,
            created_at=order.created_at,
        )
