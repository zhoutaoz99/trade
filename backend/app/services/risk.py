"""Risk service — order validation, position limits, margin checks."""

from __future__ import annotations

import logging
from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.services.market_data import market_data_service

logger = logging.getLogger(__name__)


class RiskCheckResult:
    def __init__(self, passed: bool, reason: str = ""):
        self.passed = passed
        self.reason = reason


class RiskService:
    """Validates orders against risk limits before execution."""

    def __init__(self, session: AsyncSession):
        self._session = session

    async def check_order(
        self,
        symbol: str,
        side: str,
        quantity: Decimal,
        leverage: int,
        reduce_only: bool = False,
        current_position_qty: Decimal = Decimal("0"),
        available_balance: Decimal = Decimal("0"),
    ) -> RiskCheckResult:
        # 1. Validate leverage range
        if leverage < 1 or leverage > settings.risk_max_leverage:
            return RiskCheckResult(
                False, f"Leverage {leverage} exceeds max {settings.risk_max_leverage}"
            )

        # 2. Get current price for notional calculation
        try:
            tick = await market_data_service.get_latest_book_ticker(symbol)
            price = (
                tick.ask_price if side == "BUY" else tick.bid_price
            )
        except Exception as e:
            return RiskCheckResult(False, f"No price data: {e}")

        # 3. Check order notional
        order_notional = quantity * price
        if order_notional > settings.risk_max_order_notional:
            return RiskCheckResult(
                False,
                f"Order notional {order_notional} exceeds max {settings.risk_max_order_notional}",
            )

        # 4. Check position notional (after trade)
        if side == "BUY":
            new_position_qty = current_position_qty + quantity
        else:
            new_position_qty = current_position_qty - quantity

        new_position_notional = abs(new_position_qty) * price
        if new_position_notional > settings.risk_max_position_notional:
            return RiskCheckResult(
                False,
                f"Position notional {new_position_notional} exceeds max {settings.risk_max_position_notional}",
            )

        # 5. Check margin sufficiency
        initial_margin = order_notional / Decimal(str(leverage))
        if not reduce_only and initial_margin > available_balance:
            return RiskCheckResult(
                False,
                f"Insufficient margin: need {initial_margin}, available {available_balance}",
            )

        # 6. Reduce-only check
        if reduce_only:
            if side == "BUY" and current_position_qty >= 0:
                return RiskCheckResult(
                    False, "Reduce-only BUY order but current position is not short"
                )
            if side == "SELL" and current_position_qty <= 0:
                return RiskCheckResult(
                    False, "Reduce-only SELL order but current position is not long"
                )
            if abs(quantity) > abs(current_position_qty):
                return RiskCheckResult(
                    False,
                    f"Reduce-only quantity {quantity} exceeds position {current_position_qty}",
                )

        return RiskCheckResult(True)

    async def validate_symbol_filters(
        self, symbol: str, quantity: Decimal, leverage: int
    ) -> RiskCheckResult:
        """Validate order against Binance symbol-level filters."""
        try:
            info = await market_data_service.get_symbol(symbol)
        except ValueError as e:
            return RiskCheckResult(False, str(e))

        # Check order type support
        if "MARKET" not in info.order_types:
            return RiskCheckResult(False, f"MARKET orders not supported for {symbol}")

        # Check step size
        step = info.filters.step_size
        if quantity % step != 0:
            return RiskCheckResult(
                False, f"Quantity {quantity} does not match step size {step}"
            )

        # Check min quantity
        if quantity < info.filters.min_qty:
            return RiskCheckResult(
                False, f"Quantity {quantity} below min {info.filters.min_qty}"
            )

        # Check min notional (use latest price)
        try:
            tick = await market_data_service.get_latest_book_ticker(symbol)
            mid_price = (tick.bid_price + tick.ask_price) / Decimal("2")
            notional = quantity * mid_price
            if notional < info.filters.min_notional:
                return RiskCheckResult(
                    False,
                    f"Notional {notional} below min {info.filters.min_notional}",
                )
        except Exception:
            pass  # Skip notional check if no price data; let order fail later if needed

        return RiskCheckResult(True)
