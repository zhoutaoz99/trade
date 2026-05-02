"""FastAPI application entry point for the U本位合约模拟交易系统."""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.api.routes.accounts import router as accounts_router
from app.api.routes.futures import router as futures_router
from app.core.config import settings
from app.core.logging import setup_logging
from app.services.market_data import market_data_service

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown lifecycle."""
    setup_logging()
    logger.info(
        "Starting UM Futures Sim Trading System env=%s", settings.app_env
    )
    logger.info(
        "Risk config: max_leverage=%s max_order_notional=%s max_position_notional=%s",
        settings.risk_max_leverage,
        settings.risk_max_order_notional,
        settings.risk_max_position_notional,
    )

    # Preload exchange info on startup
    try:
        await market_data_service.sync_exchange_info()
    except Exception:
        logger.warning("Could not sync exchangeInfo on startup — will retry on first use")

    # Start WebSocket market data
    await market_data_service.start_ws()

    yield

    # Shutdown
    await market_data_service.stop_ws()
    if market_data_service._http:
        await market_data_service._http.aclose()
    logger.info("UM Futures Sim Trading System shut down")


app = FastAPI(
    title="UM Futures Sim Trading System",
    description="Binance USD-M Futures simulated/live trading backend",
    version="0.1.0",
    lifespan=lifespan,
)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.exception("Unhandled exception on %s %s", request.method, request.url.path)
    return JSONResponse(
        status_code=500,
        content={"error_code": "INTERNAL_ERROR", "message": "Internal server error"},
    )


# Register routers
app.include_router(accounts_router)
app.include_router(futures_router)


@app.get("/health")
async def health_check():
    return {"status": "ok", "env": settings.app_env}
