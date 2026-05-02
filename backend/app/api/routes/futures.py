"""Futures trading REST endpoints — order, leverage, position, account queries."""

from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.schemas import (
    ClosePositionRequest,
    ErrorResponse,
    LeverageResponse,
    OrderResponse,
    PlaceOrderRequest,
    SetLeverageRequest,
)
from app.services.trading import TradingService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/futures", tags=["futures"])


@router.post("/leverage", response_model=LeverageResponse)
async def set_leverage(
    body: SetLeverageRequest,
    db: AsyncSession = Depends(get_db),
):
    """Set leverage for an account on a symbol."""
    svc = TradingService(db)
    try:
        result = await svc.set_leverage(
            account_id=body.account_id,
            symbol=body.symbol,
            leverage=body.leverage,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.exception("set_leverage failed")
        raise HTTPException(status_code=500, detail=str(e))

    return LeverageResponse(
        account_id=result.account_id,
        account_type="simulated",  # will be fixed to reflect actual type
        symbol=result.symbol,
        leverage=result.leverage,
    )


@router.post("/orders", response_model=OrderResponse, status_code=status.HTTP_201_CREATED)
async def place_order(
    body: PlaceOrderRequest,
    db: AsyncSession = Depends(get_db),
):
    """Place a MARKET order.

    Routes to simulated or live gateway based on account_type.
    """
    svc = TradingService(db)
    try:
        result = await svc.place_order(
            account_id=body.account_id,
            client_order_id=body.client_order_id,
            symbol=body.symbol,
            side=body.side.value,
            order_type=body.order_type.value,
            quantity=body.quantity,
            leverage=body.leverage,
            reduce_only=body.reduce_only,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.exception("place_order failed")
        raise HTTPException(status_code=500, detail=str(e))

    return OrderResponse(
        account_id=result.account_id,
        account_type=result.account_type,
        client_order_id=result.client_order_id,
        exchange_order_id=result.exchange_order_id,
        symbol=result.symbol,
        side=result.side,
        order_type=result.order_type,
        status=result.status,
        executed_qty=str(result.executed_qty),
        avg_price=str(result.avg_price),
        leverage=result.leverage,
        realized_pnl=str(result.realized_pnl),
        fee_amount=str(result.fee_amount),
        reduce_only=result.reduce_only,
        created_at=result.created_at,
    )


@router.post("/close-position", response_model=OrderResponse)
async def close_position(
    body: ClosePositionRequest,
    db: AsyncSession = Depends(get_db),
):
    """Close a futures position by generating a reverse MARKET reduce-only order."""
    svc = TradingService(db)
    try:
        result = await svc.close_position(
            account_id=body.account_id,
            client_order_id=body.client_order_id,
            symbol=body.symbol,
            quantity=body.quantity,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.exception("close_position failed")
        raise HTTPException(status_code=500, detail=str(e))

    return OrderResponse(
        account_id=result.account_id,
        account_type=result.account_type,
        client_order_id=result.client_order_id,
        exchange_order_id=result.exchange_order_id,
        symbol=result.symbol,
        side=result.side,
        order_type=result.order_type,
        status=result.status,
        executed_qty=str(result.executed_qty),
        avg_price=str(result.avg_price),
        leverage=result.leverage,
        realized_pnl=str(result.realized_pnl),
        fee_amount=str(result.fee_amount),
        reduce_only=result.reduce_only,
        created_at=result.created_at,
    )


@router.get("/orders/{client_order_id}", response_model=OrderResponse)
async def get_order(
    client_order_id: str,
    account_id: str = Query(..., description="Account ID"),
    db: AsyncSession = Depends(get_db),
):
    """Query an order by client_order_id and account_id."""
    svc = TradingService(db)
    try:
        result = await svc.get_order(account_id, client_order_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.exception("get_order failed")
        raise HTTPException(status_code=500, detail=str(e))

    if result is None:
        raise HTTPException(status_code=404, detail="Order not found")

    return OrderResponse(
        account_id=result.account_id,
        account_type=result.account_type,
        client_order_id=result.client_order_id,
        exchange_order_id=result.exchange_order_id,
        symbol=result.symbol,
        side=result.side,
        order_type=result.order_type,
        status=result.status,
        executed_qty=str(result.executed_qty),
        avg_price=str(result.avg_price),
        leverage=result.leverage,
        realized_pnl=str(result.realized_pnl),
        fee_amount=str(result.fee_amount),
        reduce_only=result.reduce_only,
        created_at=result.created_at,
    )


@router.get("/positions")
async def get_positions(
    account_id: str = Query(..., description="Account ID"),
    symbol: str | None = Query(None, description="Trading symbol (e.g. BTCUSDT)"),
    db: AsyncSession = Depends(get_db),
):
    """Query positions for an account, optionally filtered by symbol."""
    svc = TradingService(db)
    try:
        positions = await svc.get_positions(account_id, symbol)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.exception("get_positions failed")
        raise HTTPException(status_code=500, detail=str(e))

    return {"positions": positions}


@router.get("/account")
async def get_account_summary(
    account_id: str = Query(..., description="Account ID"),
    db: AsyncSession = Depends(get_db),
):
    """Get account summary including balances, positions, and PnL."""
    svc = TradingService(db)
    try:
        summary = await svc.get_account_summary(account_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.exception("get_account_summary failed")
        raise HTTPException(status_code=500, detail=str(e))

    return summary
