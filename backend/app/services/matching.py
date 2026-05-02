"""Simulated matching engine for MARKET order execution."""

from __future__ import annotations

import logging
import time
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.fill import Fill
from app.models.order import Order
from app.services.market_data import market_data_service
from app.services.portfolio import PortfolioService

logger = logging.getLogger(__name__)


@dataclass
class MatchResult:
    filled: bool
    fill_price: Decimal
    fill_qty: Decimal
    fee_amount: Decimal
    fee_asset: str
    realized_pnl: Decimal
    slippage_bps: int


class SimulatedMatchingEngine:
    """Executes MARKET orders against cached bookTicker prices with slippage."""

    def __init__(self, session: AsyncSession):
        self._session = session
        self._portfolio = PortfolioService(session)

    async def match_market(
        self,
        order: Order,
        account_id: uuid.UUID,
        symbol: str,
        side: str,
        quantity: Decimal,
        leverage: int,
        reduce_only: bool = False,
    ) -> MatchResult:
        """Match a MARKET order against the current order book.

        BUY  → fills at best ask + slippage
        SELL → fills at best bid - slippage
        """
        tick = await market_data_service.get_latest_book_ticker(symbol)

        slippage_bps = settings.default_slippage_bps
        slippage_factor = Decimal("1") + Decimal(str(slippage_bps)) / Decimal("10000")

        if side == "BUY":
            base_price = tick.ask_price
            fill_price = (base_price * slippage_factor).quantize(
                Decimal("0.01")  # will be refined by symbol precision
            )
        else:
            base_price = tick.bid_price
            fill_price = (base_price / slippage_factor).quantize(
                Decimal("0.01")
            )

        # Calculate fee
        fee_rate = settings.default_taker_fee_rate
        notional = quantity * fill_price
        fee_amount = (notional * fee_rate).quantize(Decimal("0.00000001"))

        # Calculate realized PnL for position reduction
        realized_pnl = Decimal("0")
        pos = await self._portfolio.get_position(account_id, symbol, "BOTH")
        if pos is not None and pos.quantity != 0:
            # Closing or reducing
            if (side == "SELL" and pos.quantity > 0) or (side == "BUY" and pos.quantity < 0):
                close_qty = min(quantity, abs(pos.quantity))
                if pos.quantity > 0:
                    realized_pnl = close_qty * (fill_price - pos.entry_price)
                else:
                    realized_pnl = close_qty * (pos.entry_price - fill_price)

        return MatchResult(
            filled=True,
            fill_price=fill_price,
            fill_qty=quantity,
            fee_amount=fee_amount,
            fee_asset="USDT",
            realized_pnl=realized_pnl,
            slippage_bps=slippage_bps,
        )

    async def execute_order(
        self,
        account_id: uuid.UUID,
        symbol: str,
        side: str,
        quantity: Decimal,
        leverage: int,
        client_order_id: str,
        reduce_only: bool = False,
    ) -> Order:
        """Execute a MARKET order atomically within the current transaction.

        Creates the order record, performs matching, records fill, updates
        position and balance, and writes ledger entries.
        """
        # Determine actual execution side based on position for close-position
        exec_side = side
        if reduce_only:
            pos = await self._portfolio.get_position(account_id, symbol, "BOTH")
            if pos is None or pos.quantity == 0:
                raise ValueError("No position to reduce")

        now = datetime.now(UTC)
        event_time_ms = int(time.time() * 1000)

        # Create order record
        order = Order(
            account_id=account_id,
            symbol=symbol,
            client_order_id=client_order_id,
            side=exec_side,
            position_side="BOTH",
            type="MARKET",
            status="NEW",
            orig_qty=quantity,
            executed_qty=Decimal("0"),
            requested_leverage=leverage,
            avg_price=Decimal("0"),
            reduce_only=reduce_only,
            close_position=False,
            raw_request={
                "symbol": symbol,
                "side": exec_side,
                "type": "MARKET",
                "quantity": str(quantity),
                "leverage": leverage,
                "reduce_only": reduce_only,
            },
        )
        self._session.add(order)
        await self._session.flush()

        # Match the order
        match_result = await self.match_market(
            order, account_id, symbol, exec_side, quantity, leverage, reduce_only
        )

        if not match_result.filled:
            order.status = "REJECTED"
            order.error_message = "No liquidity available"
            await self._session.flush()
            return order

        # Record fill
        fill = Fill(
            order_id=order.id,
            account_id=account_id,
            symbol=symbol,
            side=exec_side,
            price=match_result.fill_price,
            quantity=match_result.fill_qty,
            quote_quantity=match_result.fill_qty * match_result.fill_price,
            fee_asset=match_result.fee_asset,
            fee_amount=match_result.fee_amount,
            realized_pnl=match_result.realized_pnl,
            liquidity="taker",
            trade_time_ms=event_time_ms,
            raw_payload={
                "price": str(match_result.fill_price),
                "qty": str(match_result.fill_qty),
                "slippage_bps": match_result.slippage_bps,
            },
        )
        self._session.add(fill)
        await self._session.flush()

        # Update position
        position = await self._portfolio.update_position_on_fill(
            account_id=account_id,
            symbol=symbol,
            side=exec_side,
            fill_qty=match_result.fill_qty,
            fill_price=match_result.fill_price,
            fee_amount=match_result.fee_amount,
            realized_pnl=match_result.realized_pnl,
            leverage=leverage,
        )

        # Update balance (subtract fee)
        balance = await self._portfolio.update_balance(
            account_id, "USDT", -match_result.fee_amount
        )

        # Write ledger entries
        # Fee entry
        await self._portfolio.write_ledger(
            account_id=account_id,
            asset="USDT",
            event_type="FEE",
            amount=-match_result.fee_amount,
            balance_after=balance.wallet_balance,
            order_id=order.id,
            fill_id=fill.id,
            symbol=symbol,
            description=f"Taker fee for {exec_side} {quantity} {symbol} @ {match_result.fill_price}",
            event_time_ms=event_time_ms,
        )

        if match_result.realized_pnl != 0:
            # PnL entry
            await self._portfolio.write_ledger(
                account_id=account_id,
                asset="USDT",
                event_type="REALIZED_PNL",
                amount=match_result.realized_pnl,
                balance_after=balance.wallet_balance + match_result.realized_pnl,
                order_id=order.id,
                fill_id=fill.id,
                symbol=symbol,
                description=f"Realized PnL for {exec_side} {quantity} {symbol} @ {match_result.fill_price}",
                event_time_ms=event_time_ms,
            )

        # Update order to FILLED
        order.status = "FILLED"
        order.executed_qty = match_result.fill_qty
        order.avg_price = match_result.fill_price
        order.raw_response = {
            "status": "FILLED",
            "executedQty": str(match_result.fill_qty),
            "avgPrice": str(match_result.fill_price),
            "fee": str(match_result.fee_amount),
        }
        await self._session.flush()

        logger.info(
            "Order filled id=%s symbol=%s side=%s qty=%s price=%s fee=%s pnl=%s",
            order.id, symbol, exec_side, quantity, match_result.fill_price,
            match_result.fee_amount, match_result.realized_pnl,
        )

        return order
