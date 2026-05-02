"""Market data service — Binance exchange info sync and real-time price cache."""

from __future__ import annotations

import asyncio
import json
import logging
import time
from dataclasses import dataclass, field
from decimal import Decimal
from typing import Optional

import httpx
import websockets

from app.core.config import settings

logger = logging.getLogger(__name__)


@dataclass
class SymbolFilter:
    tick_size: Decimal = Decimal("0.01")
    step_size: Decimal = Decimal("0.001")
    min_qty: Decimal = Decimal("0.001")
    min_notional: Decimal = Decimal("5")
    market_lot_size: Optional[dict] = None


@dataclass
class SymbolInfo:
    symbol: str
    base_asset: str
    quote_asset: str
    price_precision: int
    quantity_precision: int
    filters: SymbolFilter = field(default_factory=SymbolFilter)
    order_types: list[str] = field(default_factory=lambda: ["MARKET"])
    status: str = "TRADING"


@dataclass
class BookTicker:
    symbol: str
    bid_price: Decimal
    bid_qty: Decimal
    ask_price: Decimal
    ask_qty: Decimal
    update_time_ms: int = 0


class MarketDataService:
    """Manages Binance exchange info and real-time price data.

    On first access, fetches exchangeInfo from Binance REST and caches symbol
    definitions.  WebSocket connections for bookTicker and markPrice streams are
    managed per-symbol on demand.
    """

    def __init__(self) -> None:
        self._rest_base = settings.binance_rest_base_url
        self._ws_base = settings.binance_ws_base_url
        self._http: httpx.AsyncClient | None = None

        # Symbol cache: symbol -> SymbolInfo
        self._symbols: dict[str, SymbolInfo] = {}
        self._synced: bool = False

        # Price cache: symbol -> BookTicker
        self._book_ticks: dict[str, BookTicker] = {}
        # Mark price cache: symbol -> Decimal
        self._mark_prices: dict[str, Decimal] = {}

        # WebSocket management
        self._ws_connection: Optional[websockets.WebSocketClientProtocol] = None
        self._ws_task: Optional[asyncio.Task] = None
        self._subscribed_symbols: set[str] = set()
        self._running: bool = False

    @property
    def http(self) -> httpx.AsyncClient:
        if self._http is None:
            self._http = httpx.AsyncClient(timeout=httpx.Timeout(15.0))
        return self._http

    # ─── Exchange Info ────────────────────────────────────────────────────────

    async def sync_exchange_info(self) -> None:
        """Fetch exchangeInfo from Binance and populate symbol cache."""
        url = f"{self._rest_base}/fapi/v1/exchangeInfo"
        try:
            resp = await self.http.get(url)
            resp.raise_for_status()
            data = resp.json()
        except Exception as exc:
            logger.error("Failed to fetch exchangeInfo: %s", exc)
            raise

        for s in data.get("symbols", []):
            if s.get("contractType") != "PERPETUAL":
                continue
            if s.get("status") != "TRADING":
                continue

            symbol = s["symbol"]
            filters = self._parse_filters(s.get("filters", []))
            info = SymbolInfo(
                symbol=symbol,
                base_asset=s.get("baseAsset", ""),
                quote_asset=s.get("quoteAsset", ""),
                price_precision=s.get("pricePrecision", 2),
                quantity_precision=s.get("quantityPrecision", 3),
                filters=filters,
                order_types=s.get("orderTypes", []),
                status=s["status"],
            )
            self._symbols[symbol] = info

        self._synced = True
        logger.info("exchangeInfo synced: %d perpetual symbols cached", len(self._symbols))

    @staticmethod
    def _parse_filters(filters: list[dict]) -> SymbolFilter:
        result = SymbolFilter()
        for f in filters:
            ft = f.get("filterType", "")
            if ft == "PRICE_FILTER":
                result.tick_size = Decimal(str(f.get("tickSize", "0.01")))
            elif ft == "LOT_SIZE":
                result.step_size = Decimal(str(f.get("stepSize", "0.001")))
                result.min_qty = Decimal(str(f.get("minQty", "0.001")))
            elif ft == "MIN_NOTIONAL":
                result.min_notional = Decimal(str(f.get("notional", "5")))
            elif ft == "MARKET_LOT_SIZE":
                result.market_lot_size = f
        return result

    async def ensure_synced(self) -> None:
        if not self._synced:
            await self.sync_exchange_info()

    async def get_symbol(self, symbol: str) -> SymbolInfo:
        await self.ensure_synced()
        info = self._symbols.get(symbol)
        if info is None:
            raise ValueError(f"Unknown symbol: {symbol}")
        return info

    def list_symbols(self) -> list[str]:
        return list(self._symbols.keys())

    # ─── Price Data ───────────────────────────────────────────────────────────

    async def get_latest_book_ticker(self, symbol: str) -> BookTicker:
        """Get the latest book ticker for a symbol.

        Falls back to REST if no WebSocket data is available.
        """
        tick = self._book_ticks.get(symbol)
        if tick is not None:
            return tick
        return await self._rest_book_ticker(symbol)

    async def get_latest_mark_price(self, symbol: str) -> Decimal:
        """Get the latest mark price for a symbol."""
        mp = self._mark_prices.get(symbol)
        if mp is not None:
            return mp
        return await self._rest_mark_price(symbol)

    # ─── REST Fallbacks ───────────────────────────────────────────────────────

    async def _rest_book_ticker(self, symbol: str) -> BookTicker:
        url = f"{self._rest_base}/fapi/v1/ticker/bookTicker"
        try:
            resp = await self.http.get(url, params={"symbol": symbol})
            resp.raise_for_status()
            data = resp.json()
        except Exception:
            raise RuntimeError(f"No price data available for {symbol}")

        tick = BookTicker(
            symbol=symbol,
            bid_price=Decimal(str(data["bidPrice"])),
            bid_qty=Decimal(str(data["bidQty"])),
            ask_price=Decimal(str(data["askPrice"])),
            ask_qty=Decimal(str(data["askQty"])),
            update_time_ms=int(time.time() * 1000),
        )
        self._book_ticks[symbol] = tick
        return tick

    async def _rest_mark_price(self, symbol: str) -> Decimal:
        url = f"{self._rest_base}/fapi/v1/premiumIndex"
        try:
            resp = await self.http.get(url, params={"symbol": symbol})
            resp.raise_for_status()
            data = resp.json()
        except Exception:
            raise RuntimeError(f"No mark price available for {symbol}")

        mp = Decimal(str(data["markPrice"]))
        self._mark_prices[symbol] = mp
        return mp

    # ─── WebSocket ────────────────────────────────────────────────────────────

    async def start_ws(self) -> None:
        """Start the WebSocket connection for market data streams."""
        self._running = True
        self._ws_task = asyncio.create_task(self._ws_loop())
        logger.info("Market data WebSocket task started")

    async def stop_ws(self) -> None:
        self._running = False
        if self._ws_task:
            self._ws_task.cancel()
            try:
                await self._ws_task
            except asyncio.CancelledError:
                pass
        logger.info("Market data WebSocket stopped")

    async def subscribe_symbol(self, symbol: str) -> None:
        """Subscribe to bookTicker and markPrice for a symbol."""
        symbol_lower = symbol.lower()
        if symbol_lower in self._subscribed_symbols:
            return
        self._subscribed_symbols.add(symbol_lower)
        # If WS is connected, send subscribe message
        if self._ws_connection and self._ws_connection.state.name == "OPEN":
            await self._send_subscribe([symbol_lower])

    async def _send_subscribe(self, symbols: list[str]) -> None:
        if not self._ws_connection:
            return
        streams = []
        for s in symbols:
            streams.append(f"{s}@bookTicker")
            streams.append(f"{s}@markPrice")
        msg = {
            "method": "SUBSCRIBE",
            "params": streams,
            "id": int(time.time() * 1000),
        }
        try:
            await self._ws_connection.send(json.dumps(msg))
        except Exception:
            logger.warning("Failed to send WebSocket subscribe message")

    async def _ws_loop(self) -> None:
        """Main WebSocket event loop with reconnection."""
        url = f"{self._ws_base}/ws"
        backoff = 1.0
        max_backoff = 60.0

        while self._running:
            try:
                async with websockets.connect(url, ping_interval=20) as ws:
                    self._ws_connection = ws
                    backoff = 1.0
                    logger.info("Market data WebSocket connected")

                    # Re-subscribe to any previously subscribed symbols
                    if self._subscribed_symbols:
                        await self._send_subscribe(list(self._subscribed_symbols))

                    async for message in ws:
                        if not self._running:
                            break
                        self._handle_ws_message(message)

            except asyncio.CancelledError:
                break
            except Exception as exc:
                logger.warning("WebSocket disconnected: %s — reconnecting in %.1fs", exc, backoff)
                self._ws_connection = None
                await asyncio.sleep(backoff)
                backoff = min(backoff * 1.5, max_backoff)

    def _handle_ws_message(self, raw: str) -> None:
        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            return

        # Stream data is wrapped with a "stream" key for combined streams
        stream_name = data.get("stream", "")
        stream_data = data.get("data", data)  # fallback to raw if not combined

        if stream_name.endswith("@bookTicker") or "bookTicker" in stream_name:
            self._handle_book_ticker(stream_data)
        elif stream_name.endswith("@markPrice") or "markPrice" in stream_name:
            self._handle_mark_price(stream_data)

    def _handle_book_ticker(self, data: dict) -> None:
        symbol = data.get("s", "")
        if not symbol:
            return
        tick = BookTicker(
            symbol=symbol,
            bid_price=Decimal(str(data.get("b", 0))),
            bid_qty=Decimal(str(data.get("B", 0))),
            ask_price=Decimal(str(data.get("a", 0))),
            ask_qty=Decimal(str(data.get("A", 0))),
            update_time_ms=int(time.time() * 1000),
        )
        self._book_ticks[symbol] = tick

    def _handle_mark_price(self, data: dict) -> None:
        symbol = data.get("s", "")
        mp_str = data.get("p", "")
        if symbol and mp_str:
            self._mark_prices[symbol] = Decimal(str(mp_str))


# Global singleton
market_data_service = MarketDataService()
