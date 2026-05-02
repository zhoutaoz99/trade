"""Pydantic schemas for API request/response validation."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


# ─── Enums ────────────────────────────────────────────────────────────────────

class AccountType(str, Enum):
    simulated = "simulated"
    live = "live"


class OrderSide(str, Enum):
    BUY = "BUY"
    SELL = "SELL"


class OrderType(str, Enum):
    MARKET = "MARKET"


class OrderStatus(str, Enum):
    NEW = "NEW"
    FILLED = "FILLED"
    REJECTED = "REJECTED"
    EXPIRED = "EXPIRED"


class MarginType(str, Enum):
    cross = "cross"
    isolated = "isolated"


# ─── Account ──────────────────────────────────────────────────────────────────

class CreateAccountRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    account_type: AccountType
    quote_asset: str = Field(default="USDT")
    initial_balance: Decimal = Field(default=Decimal("10000"), ge=0)
    api_key: Optional[str] = None
    api_secret: Optional[str] = None


class AccountResponse(BaseModel):
    id: str
    name: str
    account_type: AccountType
    quote_asset: str
    initial_balance: str
    status: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# ─── Leverage ─────────────────────────────────────────────────────────────────

class SetLeverageRequest(BaseModel):
    account_id: str = Field(..., min_length=1)
    symbol: str = Field(..., min_length=1)
    leverage: int = Field(..., ge=1, le=125)


class LeverageResponse(BaseModel):
    account_id: str
    account_type: str
    symbol: str
    leverage: int


# ─── Order ────────────────────────────────────────────────────────────────────

class PlaceOrderRequest(BaseModel):
    account_id: str = Field(..., min_length=1)
    client_order_id: str = Field(..., min_length=1)
    symbol: str = Field(..., min_length=1)
    side: OrderSide
    order_type: OrderType = OrderType.MARKET
    quantity: Decimal = Field(..., gt=0)
    leverage: Optional[int] = Field(default=None, ge=1, le=125)
    reduce_only: bool = False


class ClosePositionRequest(BaseModel):
    account_id: str = Field(..., min_length=1)
    client_order_id: str = Field(..., min_length=1)
    symbol: str = Field(..., min_length=1)
    quantity: Decimal = Field(..., gt=0)


class OrderResponse(BaseModel):
    account_id: str
    account_type: str
    client_order_id: str
    exchange_order_id: Optional[str] = None
    symbol: str
    side: str
    order_type: str
    status: str
    executed_qty: str
    avg_price: str
    leverage: Optional[int] = None
    realized_pnl: str = "0"
    fee_amount: str = "0"
    reduce_only: bool = False
    created_at: datetime


class OrderQuery(BaseModel):
    account_id: str = Field(..., min_length=1)


# ─── Position ─────────────────────────────────────────────────────────────────

class PositionResponse(BaseModel):
    account_id: str
    symbol: str
    position_side: str
    quantity: str
    entry_price: str
    breakeven_price: str
    leverage: int
    margin_type: str
    isolated_margin: str
    unrealized_pnl: str
    realized_pnl: str


class PositionQuery(BaseModel):
    account_id: str = Field(..., min_length=1)
    symbol: Optional[str] = None


# ─── Account Summary ──────────────────────────────────────────────────────────

class BalanceItem(BaseModel):
    asset: str
    wallet_balance: str
    available_balance: str
    margin_balance: str
    unrealized_pnl: str


class AccountSummaryResponse(BaseModel):
    account_id: str
    account_type: str
    quote_asset: str
    balances: list[BalanceItem]
    positions: list[PositionResponse]
    total_unrealized_pnl: str
    total_realized_pnl: str
    total_pnl: str
    daily_pnl: str
    monthly_pnl: str
    total_margin_used: str


# ─── Account Query ────────────────────────────────────────────────────────────

class AccountQuery(BaseModel):
    account_id: str = Field(..., min_length=1)


# ─── Error ────────────────────────────────────────────────────────────────────

class ErrorResponse(BaseModel):
    error_code: str
    message: str
    details: Optional[dict] = None
