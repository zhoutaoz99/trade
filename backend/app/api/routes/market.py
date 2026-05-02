"""Market data REST endpoints — current price queries."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query

from app.services.market_data import market_data_service

router = APIRouter(prefix="/api/v1/market", tags=["market"])


@router.get("/price")
async def get_price(
    symbol: str = Query(..., description="Trading symbol, e.g. BTCUSDT"),
):
    """Get current mark price and bid/ask for a symbol."""
    try:
        tick = await market_data_service.get_latest_book_ticker(symbol.upper())
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    return {
        "symbol": symbol.upper(),
        "ask_price": str(tick.ask_price),
        "bid_price": str(tick.bid_price),
    }
