"""Portfolio service — account balances, positions, PnL calculation."""

from __future__ import annotations

import logging
import uuid
from decimal import Decimal
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.crypto import encrypt_api_secret, decrypt_api_secret
from app.models.account import Account
from app.models.account_credential import AccountCredential
from app.models.balance import Balance
from app.models.ledger_entry import LedgerEntry
from app.models.position import Position
from app.services.market_data import market_data_service

logger = logging.getLogger(__name__)


class PortfolioService:
    """Manages account balances, positions, and PnL for simulated accounts."""

    def __init__(self, session: AsyncSession):
        self._session = session

    # ─── Account CRUD ─────────────────────────────────────────────────────────

    async def create_account(
        self,
        name: str,
        account_type: str,
        quote_asset: str = "USDT",
        initial_balance: Optional[Decimal] = None,
        api_key: Optional[str] = None,
        api_secret: Optional[str] = None,
    ) -> Account:
        if initial_balance is None:
            initial_balance = settings.default_account_initial_balance

        account = Account(
            name=name,
            account_type=account_type,
            quote_asset=quote_asset,
            initial_balance=initial_balance,
        )
        self._session.add(account)
        await self._session.flush()

        if account_type == "simulated":
            await self._init_balance(account.id, quote_asset, initial_balance)

        if account_type == "live" and api_key and api_secret:
            encrypted = encrypt_api_secret(api_secret)
            cred = AccountCredential(
                account_id=account.id,
                api_key=api_key,
                encrypted_api_secret=encrypted,
            )
            self._session.add(cred)
            await self._session.flush()

        logger.info(
            "Account created id=%s type=%s name=%s", account.id, account_type, name
        )
        return account

    async def get_account(self, account_id: uuid.UUID) -> Account:
        stmt = select(Account).where(Account.id == account_id)
        result = await self._session.execute(stmt)
        account = result.scalar_one_or_none()
        if account is None:
            raise ValueError(f"Account not found: {account_id}")
        return account

    async def get_credential(self, account_id: uuid.UUID) -> Optional[AccountCredential]:
        stmt = select(AccountCredential).where(AccountCredential.account_id == account_id)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_decrypted_secret(self, account_id: uuid.UUID) -> Optional[str]:
        cred = await self.get_credential(account_id)
        if cred is None:
            return None
        return decrypt_api_secret(cred.encrypted_api_secret)

    # ─── Balance ──────────────────────────────────────────────────────────────

    async def _init_balance(
        self, account_id: uuid.UUID, asset: str, amount: Decimal
    ) -> Balance:
        balance = Balance(
            account_id=account_id,
            asset=asset,
            wallet_balance=amount,
            available_balance=amount,
            margin_balance=amount,
            unrealized_pnl=Decimal("0"),
        )
        self._session.add(balance)
        await self._session.flush()
        return balance

    async def get_balance(self, account_id: uuid.UUID, asset: str = "USDT") -> Balance:
        stmt = select(Balance).where(
            Balance.account_id == account_id, Balance.asset == asset
        )
        result = await self._session.execute(stmt)
        balance = result.scalar_one_or_none()
        if balance is None:
            raise ValueError(f"Balance not found: {account_id}/{asset}")
        return balance

    async def update_balance(
        self,
        account_id: uuid.UUID,
        asset: str,
        delta: Decimal,
    ) -> Balance:
        """Apply a delta to wallet_balance and available_balance."""
        balance = await self.get_balance(account_id, asset)
        balance.wallet_balance += delta
        balance.available_balance += delta
        balance.margin_balance = balance.wallet_balance + balance.unrealized_pnl
        await self._session.flush()
        return balance

    async def lock_margin(
        self, account_id: uuid.UUID, asset: str, amount: Decimal
    ) -> Balance:
        """Move funds from available to margin."""
        balance = await self.get_balance(account_id, asset)
        if balance.available_balance < amount:
            raise ValueError("Insufficient available balance for margin")
        balance.available_balance -= amount
        await self._session.flush()
        return balance

    async def unlock_margin(
        self, account_id: uuid.UUID, asset: str, amount: Decimal
    ) -> Balance:
        """Return margin to available balance."""
        balance = await self.get_balance(account_id, asset)
        balance.available_balance += amount
        await self._session.flush()
        return balance

    # ─── Position ─────────────────────────────────────────────────────────────

    async def get_position(
        self, account_id: uuid.UUID, symbol: str, position_side: str = "BOTH"
    ) -> Optional[Position]:
        stmt = select(Position).where(
            Position.account_id == account_id,
            Position.symbol == symbol,
            Position.position_side == position_side,
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_all_positions(self, account_id: uuid.UUID) -> list[Position]:
        stmt = select(Position).where(Position.account_id == account_id)
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def get_or_create_position(
        self,
        account_id: uuid.UUID,
        symbol: str,
        leverage: int,
        position_side: str = "BOTH",
        margin_type: str = "cross",
    ) -> Position:
        pos = await self.get_position(account_id, symbol, position_side)
        if pos is None:
            pos = Position(
                account_id=account_id,
                symbol=symbol,
                position_side=position_side,
                quantity=Decimal("0"),
                entry_price=Decimal("0"),
                breakeven_price=Decimal("0"),
                leverage=leverage,
                margin_type=margin_type,
            )
            self._session.add(pos)
            await self._session.flush()
        return pos

    async def update_position_on_fill(
        self,
        account_id: uuid.UUID,
        symbol: str,
        side: str,  # BUY or SELL
        fill_qty: Decimal,
        fill_price: Decimal,
        fee_amount: Decimal,
        realized_pnl: Decimal,
        leverage: int,
    ) -> Position:
        """Update position after a fill using one-way mode logic."""
        pos = await self.get_position(account_id, symbol, "BOTH")

        if pos is None or pos.quantity == Decimal("0"):
            # Opening a new position
            pos = await self.get_or_create_position(account_id, symbol, leverage)
            if side == "BUY":
                pos.quantity = fill_qty
            else:
                pos.quantity = -fill_qty
            pos.entry_price = fill_price
        else:
            current_qty = pos.quantity
            if side == "BUY":
                new_qty = current_qty + fill_qty
            else:
                new_qty = current_qty - fill_qty

            # Same direction or crossing zero
            if (current_qty > 0 and new_qty >= 0) or (current_qty < 0 and new_qty <= 0):
                # Adding to position or partially reducing
                if current_qty != 0:
                    # Weighted average entry price for additions
                    abs_old = abs(current_qty)
                    abs_new = abs(new_qty)
                    if abs_new > abs_old:  # adding
                        old_notional = abs_old * pos.entry_price
                        added_notional = (abs_new - abs_old) * fill_price
                        pos.entry_price = (old_notional + added_notional) / abs_new
                    # For partial reduction, entry_price stays the same
                pos.quantity = new_qty
            else:
                # Position crossed zero — close old and open new
                pos.quantity = new_qty
                if new_qty != 0:
                    pos.entry_price = fill_price
                else:
                    pos.entry_price = Decimal("0")

        # Update realized PnL and breakeven
        pos.realized_pnl += realized_pnl

        if pos.quantity != 0:
            fee_per_unit = fee_amount / fill_qty
            if pos.quantity > 0:
                pos.breakeven_price = pos.entry_price + fee_per_unit * Decimal("2")
            else:
                pos.breakeven_price = pos.entry_price - fee_per_unit * Decimal("2")
        else:
            pos.breakeven_price = Decimal("0")

        # Update unrealized PnL
        try:
            mark_price = await market_data_service.get_latest_mark_price(symbol)
            pos.unrealized_pnl = self._calc_unrealized_pnl(pos.quantity, pos.entry_price, mark_price)
        except Exception:
            pos.unrealized_pnl = Decimal("0")

        pos.leverage = leverage
        await self._session.flush()
        return pos

    # ─── PnL Calculation ──────────────────────────────────────────────────────

    @staticmethod
    def _calc_unrealized_pnl(
        quantity: Decimal, entry_price: Decimal, mark_price: Decimal
    ) -> Decimal:
        if quantity == 0 or entry_price == 0:
            return Decimal("0")
        if quantity > 0:
            return quantity * (mark_price - entry_price)
        else:
            return abs(quantity) * (entry_price - mark_price)

    async def calculate_unrealized_pnl(
        self, account_id: uuid.UUID, symbol: str
    ) -> Decimal:
        pos = await self.get_position(account_id, symbol)
        if pos is None or pos.quantity == 0:
            return Decimal("0")
        try:
            mark_price = await market_data_service.get_latest_mark_price(symbol)
        except Exception:
            mark_price = pos.entry_price
        return self._calc_unrealized_pnl(pos.quantity, pos.entry_price, mark_price)

    # ─── Ledger ───────────────────────────────────────────────────────────────

    async def write_ledger(
        self,
        account_id: uuid.UUID,
        asset: str,
        event_type: str,
        amount: Decimal,
        balance_after: Decimal,
        order_id: Optional[uuid.UUID] = None,
        fill_id: Optional[uuid.UUID] = None,
        symbol: Optional[str] = None,
        description: Optional[str] = None,
        event_time_ms: Optional[int] = None,
    ) -> LedgerEntry:
        import time as _time
        if event_time_ms is None:
            event_time_ms = int(_time.time() * 1000)

        entry = LedgerEntry(
            account_id=account_id,
            asset=asset,
            event_type=event_type,
            amount=amount,
            balance_after=balance_after,
            order_id=order_id,
            fill_id=fill_id,
            symbol=symbol,
            description=description,
            event_time_ms=event_time_ms,
        )
        self._session.add(entry)
        await self._session.flush()
        return entry
