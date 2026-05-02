"""Abstract exchange gateway interface."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Optional


@dataclass
class LeverageResult:
    account_id: str
    symbol: str
    leverage: int


@dataclass
class OrderResult:
    account_id: str
    account_type: str
    client_order_id: str
    exchange_order_id: Optional[str]
    symbol: str
    side: str
    order_type: str
    status: str
    executed_qty: Decimal
    avg_price: Decimal
    leverage: Optional[int]
    realized_pnl: Decimal
    fee_amount: Decimal
    reduce_only: bool
    created_at: datetime


class ExchangeGateway(ABC):
    @abstractmethod
    async def set_leverage(self, account_id: str, symbol: str, leverage: int) -> LeverageResult:
        ...

    @abstractmethod
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
        ...

    @abstractmethod
    async def close_position(
        self,
        account_id: str,
        client_order_id: str,
        symbol: str,
        quantity: Decimal,
    ) -> OrderResult:
        ...
