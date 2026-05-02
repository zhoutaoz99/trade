"""Trading service — validation, risk checks, and account-type routing."""

from __future__ import annotations

import logging
import uuid
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from typing import Optional

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.gateways.base import ExchangeGateway, LeverageResult, OrderResult
from app.gateways.simulated import SimulatedExchangeGateway
from app.gateways.binance import BinanceFuturesGateway
from app.models.account import Account
from app.models.order import Order
from app.models.position import Position
from app.models.balance import Balance
from app.models.fill import Fill
from app.core.config import settings
from app.services.market_data import market_data_service
from app.services.portfolio import PortfolioService
from app.services.risk import RiskService

logger = logging.getLogger(__name__)


class TradingService:
    """Validates and routes orders to the correct exchange gateway.

    Loads account by ID, checks account_type, and delegates to either
    SimulatedExchangeGateway or BinanceFuturesGateway.
    """

    def __init__(self, session: AsyncSession):
        self._session = session
        self._portfolio = PortfolioService(session)
        self._risk = RiskService(session)

    async def _load_account(self, account_id: str) -> Account:
        aid = uuid.UUID(account_id)
        return await self._portfolio.get_account(aid)

    async def _get_gateway(self, account_id: str) -> ExchangeGateway:
        account = await self._load_account(account_id)
        if account.account_type == "simulated":
            return SimulatedExchangeGateway(self._session)
        elif account.account_type == "live":
            cred = await self._portfolio.get_credential(account.id)
            if cred is None:
                raise ValueError("Live account has no API credentials configured")
            from app.core.crypto import decrypt_api_secret
            api_secret = decrypt_api_secret(cred.encrypted_api_secret)
            return BinanceFuturesGateway(
                api_key=cred.api_key,
                api_secret=api_secret,
            )
        else:
            raise ValueError(f"Unknown account type: {account.account_type}")

    # ─── Set Leverage ─────────────────────────────────────────────────────────

    async def set_leverage(
        self, account_id: str, symbol: str, leverage: int
    ) -> LeverageResult:
        account = await self._load_account(account_id)

        # Validate leverage against risk limits
        if leverage < 1 or leverage > settings.risk_max_leverage:
            raise ValueError(f"Leverage {leverage} exceeds max {settings.risk_max_leverage}")

        gateway = await self._get_gateway(account_id)
        result = await gateway.set_leverage(account_id, symbol, leverage)

        logger.info(
            "Leverage set account=%s type=%s symbol=%s leverage=%d",
            account_id, account.account_type, symbol, leverage,
        )
        return result

    # ─── Place Order ──────────────────────────────────────────────────────────

    async def place_order(
        self,
        account_id: str,
        client_order_id: str,
        symbol: str,
        side: str,
        order_type: str,
        quantity: Decimal,
        leverage: Optional[int] = None,
        reduce_only: bool = False,
    ) -> OrderResult:
        account = await self._load_account(account_id)

        # Validate order_type
        if order_type != "MARKET":
            raise ValueError("Only MARKET orders are supported in this version")

        # Validate side
        if side not in ("BUY", "SELL"):
            raise ValueError("side must be BUY or SELL")

        # Validate symbol filters
        symbol_check = await self._risk.validate_symbol_filters(symbol, quantity, leverage or 1)
        if not symbol_check.passed:
            raise ValueError(symbol_check.reason)

        # Determine effective leverage
        effective_leverage = leverage
        if effective_leverage is None:
            # Use existing position leverage or default
            pos = await self._portfolio.get_position(account.id, symbol, "BOTH")
            effective_leverage = pos.leverage if pos else 1

        # Risk check
        current_qty = Decimal("0")
        if account.account_type == "simulated":
            pos = await self._portfolio.get_position(account.id, symbol, "BOTH")
            if pos:
                current_qty = pos.quantity

            balance = await self._portfolio.get_balance(account.id, "USDT")
            available = balance.available_balance
        else:
            # For live accounts, risk check is more lenient — Binance does its own checks
            available = Decimal("999999999")

        risk_result = await self._risk.check_order(
            symbol=symbol,
            side=side,
            quantity=quantity,
            leverage=effective_leverage,
            reduce_only=reduce_only,
            current_position_qty=current_qty,
            available_balance=available,
        )
        if not risk_result.passed:
            raise ValueError(risk_result.reason)

        # Route to gateway
        gateway = await self._get_gateway(account_id)
        result = await gateway.place_order(
            account_id=account_id,
            client_order_id=client_order_id,
            symbol=symbol,
            side=side,
            order_type=order_type,
            quantity=quantity,
            leverage=effective_leverage,
            reduce_only=reduce_only,
        )

        logger.info(
            "Order placed account=%s type=%s client_oid=%s symbol=%s side=%s qty=%s status=%s",
            account_id, account.account_type, client_order_id, symbol, side, quantity, result.status,
        )
        return result

    # ─── Close Position ───────────────────────────────────────────────────────

    async def close_position(
        self,
        account_id: str,
        client_order_id: str,
        symbol: str,
        quantity: Decimal,
    ) -> OrderResult:
        account = await self._load_account(account_id)

        if account.account_type == "simulated":
            pos = await self._portfolio.get_position(account.id, symbol, "BOTH")
            if pos is None or pos.quantity == 0:
                raise ValueError(f"No open position for {symbol}")
            if quantity > abs(pos.quantity):
                raise ValueError(
                    f"Close quantity {quantity} exceeds position {pos.quantity}"
                )

        gateway = await self._get_gateway(account_id)
        result = await gateway.close_position(
            account_id=account_id,
            client_order_id=client_order_id,
            symbol=symbol,
            quantity=quantity,
        )

        logger.info(
            "Position closed account=%s type=%s symbol=%s qty=%s",
            account_id, account.account_type, symbol, quantity,
        )
        return result

    # ─── Query ────────────────────────────────────────────────────────────────

    async def list_orders(
        self,
        account_id: str,
        symbol: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[OrderResult]:
        """List orders for an account, newest first."""
        account = await self._load_account(account_id)
        aid = account.id

        stmt = select(Order).where(Order.account_id == aid)
        if symbol:
            stmt = stmt.where(Order.symbol == symbol)
        stmt = stmt.order_by(Order.created_at.desc()).limit(limit).offset(offset)
        result = await self._session.execute(stmt)
        orders = result.scalars().all()

        results = []
        for order in orders:
            # Aggregate fees from fills
            fill_stmt = select(Fill).where(Fill.order_id == order.id)
            fill_result = await self._session.execute(fill_stmt)
            fills = fill_result.scalars().all()

            total_fee = sum((f.fee_amount for f in fills), Decimal("0"))
            total_pnl = sum((f.realized_pnl for f in fills), Decimal("0"))

            results.append(OrderResult(
                account_id=account_id,
                account_type=account.account_type,
                client_order_id=order.client_order_id,
                exchange_order_id=order.exchange_order_id,
                symbol=order.symbol,
                side=order.side,
                order_type=order.type,
                status=order.status,
                executed_qty=order.executed_qty,
                avg_price=order.avg_price,
                leverage=order.requested_leverage,
                realized_pnl=total_pnl,
                fee_amount=total_fee,
                reduce_only=order.reduce_only,
                created_at=order.created_at,
            ))

        return results

    async def get_order(
        self, account_id: str, client_order_id: str
    ) -> Optional[OrderResult]:
        account = await self._load_account(account_id)
        aid = account.id

        if account.account_type == "simulated":
            stmt = select(Order).where(
                Order.account_id == aid,
                Order.client_order_id == client_order_id,
            )
            result = await self._session.execute(stmt)
            order = result.scalar_one_or_none()
            if order is None:
                return None

            # Aggregate fees from fills
            fill_stmt = select(Fill).where(Fill.order_id == order.id)
            fill_result = await self._session.execute(fill_stmt)
            fills = fill_result.scalars().all()

            total_fee = sum((f.fee_amount for f in fills), Decimal("0"))
            total_pnl = sum((f.realized_pnl for f in fills), Decimal("0"))

            return OrderResult(
                account_id=account_id,
                account_type="simulated",
                client_order_id=order.client_order_id,
                exchange_order_id=order.exchange_order_id,
                symbol=order.symbol,
                side=order.side,
                order_type=order.type,
                status=order.status,
                executed_qty=order.executed_qty,
                avg_price=order.avg_price,
                leverage=order.requested_leverage,
                realized_pnl=total_pnl,
                fee_amount=total_fee,
                reduce_only=order.reduce_only,
                created_at=order.created_at,
            )
        else:
            # Live account: query Binance directly
            gateway = await self._get_gateway(account_id)
            assert isinstance(gateway, BinanceFuturesGateway)
            return await gateway.query_order(symbol="", client_order_id=client_order_id)

    async def get_positions(
        self, account_id: str, symbol: Optional[str] = None
    ) -> list[dict]:
        account = await self._load_account(account_id)
        aid = account.id

        if account.account_type == "simulated":
            if symbol:
                stmt = select(Position).where(
                    Position.account_id == aid,
                    Position.symbol == symbol,
                )
            else:
                stmt = select(Position).where(Position.account_id == aid)
            result = await self._session.execute(stmt)
            positions = result.scalars().all()

            # Recalculate unrealized PnL with live mark prices
            pnl_results = []
            for p in positions:
                if p.quantity != 0:
                    try:
                        live_pnl = await self._portfolio.calculate_unrealized_pnl(aid, p.symbol)
                    except Exception:
                        live_pnl = p.unrealized_pnl
                else:
                    live_pnl = Decimal("0")
                pnl_results.append(
                    {
                        "account_id": account_id,
                        "symbol": p.symbol,
                        "position_side": p.position_side,
                        "quantity": str(p.quantity),
                        "entry_price": str(p.entry_price),
                        "breakeven_price": str(p.breakeven_price),
                        "leverage": p.leverage,
                        "margin_type": p.margin_type,
                        "isolated_margin": str(p.isolated_margin),
                        "unrealized_pnl": str(live_pnl),
                        "realized_pnl": str(p.realized_pnl),
                    }
                )
            return pnl_results
        else:
            # Live account: query Binance REST
            cred = await self._portfolio.get_credential(aid)
            if cred is None:
                raise ValueError("Live account has no API credentials")
            from app.core.crypto import decrypt_api_secret
            api_secret = decrypt_api_secret(cred.encrypted_api_secret)

            import httpx
            from app.core.config import settings as cfg
            import hashlib
            import hmac
            import time

            params: dict = {
                "timestamp": int(time.time() * 1000),
                "recvWindow": cfg.binance_recv_window,
            }
            if symbol:
                params["symbol"] = symbol
            query = "&".join(f"{k}={v}" for k, v in sorted(params.items()))
            signature = hmac.new(
                api_secret.encode(), query.encode(), hashlib.sha256
            ).hexdigest()
            params["signature"] = signature

            async with httpx.AsyncClient() as client:
                resp = await client.get(
                    f"{cfg.binance_rest_base_url}/fapi/v2/positionRisk",
                    params=params,
                    headers={"X-MBX-APIKEY": cred.api_key},
                )
                resp.raise_for_status()
                data = resp.json()

            return [
                {
                    "account_id": account_id,
                    "symbol": p.get("symbol", ""),
                    "position_side": p.get("positionSide", "BOTH"),
                    "quantity": p.get("positionAmt", "0"),
                    "entry_price": p.get("entryPrice", "0"),
                    "breakeven_price": p.get("breakEvenPrice", "0"),
                    "leverage": int(p.get("leverage", 1)),
                    "margin_type": p.get("marginType", "cross"),
                    "isolated_margin": p.get("isolatedMargin", "0"),
                    "unrealized_pnl": p.get("unRealizedProfit", "0"),
                    "realized_pnl": "0",
                }
                for p in data
            ]

    async def get_account_summary(self, account_id: str) -> dict:
        account = await self._load_account(account_id)
        aid = account.id

        if account.account_type == "simulated":
            balances_stmt = select(Balance).where(Balance.account_id == aid)
            balances_result = await self._session.execute(balances_stmt)
            balances = balances_result.scalars().all()

            positions_stmt = select(Position).where(Position.account_id == aid)
            positions_result = await self._session.execute(positions_stmt)
            positions = positions_result.scalars().all()

            # Recalculate unrealized PnL with live mark prices
            live_pnls: dict[str, Decimal] = {}
            total_unrealized = Decimal("0")
            for p in positions:
                if p.quantity != 0:
                    try:
                        live_pnl = await self._portfolio.calculate_unrealized_pnl(aid, p.symbol)
                    except Exception:
                        live_pnl = p.unrealized_pnl
                else:
                    live_pnl = Decimal("0")
                live_pnls[p.symbol] = live_pnl
                total_unrealized += live_pnl

            total_margin = sum(
                (abs(p.quantity) * p.entry_price / Decimal(str(p.leverage))
                 for p in positions if p.quantity != 0),
                Decimal("0"),
            )

            # Total realized P&L (all-time, net of fees)
            total_realized = Decimal("0")
            total_realized_row = await self._session.execute(
                select(func.coalesce(func.sum(Fill.realized_pnl - Fill.fee_amount), 0))
                .where(Fill.account_id == aid)
            )
            total_realized = Decimal(str(total_realized_row.scalar()))

            # Daily P&L (today UTC, net of fees)
            today_start = datetime.now(UTC).replace(hour=0, minute=0, second=0, microsecond=0)
            daily_row = await self._session.execute(
                select(func.coalesce(func.sum(Fill.realized_pnl - Fill.fee_amount), 0))
                .where(Fill.account_id == aid, Fill.created_at >= today_start)
            )
            daily_pnl = Decimal(str(daily_row.scalar()))

            # Monthly P&L (this month UTC, net of fees)
            month_start = today_start.replace(day=1)
            monthly_row = await self._session.execute(
                select(func.coalesce(func.sum(Fill.realized_pnl - Fill.fee_amount), 0))
                .where(Fill.account_id == aid, Fill.created_at >= month_start)
            )
            monthly_pnl = Decimal(str(monthly_row.scalar()))

            total_pnl = total_realized + total_unrealized

            return {
                "account_id": account_id,
                "account_type": account.account_type,
                "quote_asset": account.quote_asset,
                "balances": [
                    {
                        "asset": b.asset,
                        "wallet_balance": str(b.wallet_balance),
                        "available_balance": str(b.available_balance),
                        "margin_balance": str(b.margin_balance),
                        "unrealized_pnl": str(b.unrealized_pnl),
                    }
                    for b in balances
                ],
                "positions": [
                    {
                        "account_id": account_id,
                        "symbol": p.symbol,
                        "position_side": p.position_side,
                        "quantity": str(p.quantity),
                        "entry_price": str(p.entry_price),
                        "breakeven_price": str(p.breakeven_price),
                        "leverage": p.leverage,
                        "margin_type": p.margin_type,
                        "isolated_margin": str(p.isolated_margin),
                        "unrealized_pnl": str(live_pnls[p.symbol]),
                        "realized_pnl": str(p.realized_pnl),
                    }
                    for p in positions
                ],
                "total_unrealized_pnl": str(total_unrealized),
                "total_realized_pnl": str(total_realized),
                "total_pnl": str(total_pnl),
                "daily_pnl": str(daily_pnl),
                "monthly_pnl": str(monthly_pnl),
                "total_margin_used": str(total_margin),
            }
        else:
            # Live account: query Binance
            cred = await self._portfolio.get_credential(aid)
            if cred is None:
                raise ValueError("Live account has no API credentials")
            from app.core.crypto import decrypt_api_secret
            api_secret = decrypt_api_secret(cred.encrypted_api_secret)

            import httpx
            from app.core.config import settings as cfg
            import hashlib
            import hmac
            import time as _time

            ts = int(_time.time() * 1000)
            params = {
                "timestamp": ts,
                "recvWindow": cfg.binance_recv_window,
            }
            query = "&".join(f"{k}={v}" for k, v in sorted(params.items()))
            signature = hmac.new(
                api_secret.encode(), query.encode(), hashlib.sha256
            ).hexdigest()
            params["signature"] = signature

            async with httpx.AsyncClient() as client:
                resp = await client.get(
                    f"{cfg.binance_rest_base_url}/fapi/v2/account",
                    params=params,
                    headers={"X-MBX-APIKEY": cred.api_key},
                )
                resp.raise_for_status()
                data = resp.json()

            assets = data.get("assets", [])
            positions_raw = data.get("positions", [])

            return {
                "account_id": account_id,
                "account_type": account.account_type,
                "quote_asset": account.quote_asset,
                "balances": [
                    {
                        "asset": a.get("asset", ""),
                        "wallet_balance": a.get("walletBalance", "0"),
                        "available_balance": a.get("availableBalance", "0"),
                        "margin_balance": a.get("marginBalance", "0"),
                        "unrealized_pnl": a.get("unrealizedProfit", "0"),
                    }
                    for a in assets
                ],
                "positions": [
                    {
                        "account_id": account_id,
                        "symbol": p.get("symbol", ""),
                        "position_side": p.get("positionSide", "BOTH"),
                        "quantity": p.get("positionAmt", "0"),
                        "entry_price": p.get("entryPrice", "0"),
                        "breakeven_price": p.get("breakEvenPrice", "0"),
                        "leverage": int(p.get("leverage", 1)),
                        "margin_type": p.get("marginType", "cross"),
                        "isolated_margin": p.get("isolatedMargin", "0"),
                        "unrealized_pnl": p.get("unRealizedProfit", "0"),
                        "realized_pnl": "0",
                    }
                    for p in positions_raw
                ],
                "total_unrealized_pnl": data.get("totalUnrealizedProfit", "0"),
                "total_realized_pnl": "0",
                "total_pnl": data.get("totalUnrealizedProfit", "0"),
                "daily_pnl": "0",
                "monthly_pnl": "0",
                "total_margin_used": data.get("totalMarginBalance", "0"),
            }
