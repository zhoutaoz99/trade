"""Binance live futures gateway — real trading via Binance REST API."""

from __future__ import annotations

import hashlib
import hmac
import logging
import time
from datetime import UTC, datetime
from decimal import Decimal
from typing import Optional
from urllib.parse import urlencode

import httpx

from app.core.config import settings
from app.gateways.base import ExchangeGateway, LeverageResult, OrderResult

logger = logging.getLogger(__name__)


class BinanceFuturesGateway(ExchangeGateway):
    """Handles trading operations for live accounts via Binance USD-M Futures API.

    Requires API key and secret configured on the account.
    """

    def __init__(
        self,
        api_key: str,
        api_secret: str,
        http_client: Optional[httpx.AsyncClient] = None,
    ):
        self._api_key = api_key
        self._api_secret = api_secret
        self._rest_base = settings.binance_rest_base_url
        self._recv_window = settings.binance_recv_window
        self._http = http_client or httpx.AsyncClient(timeout=httpx.Timeout(15.0))

    # ─── Signature ────────────────────────────────────────────────────────────

    def _sign(self, params: dict) -> str:
        query = urlencode(params)
        return hmac.new(
            self._api_secret.encode("utf-8"),
            query.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()

    def _signed_request_params(self, extra: dict | None = None) -> dict:
        params = {
            "timestamp": int(time.time() * 1000),
            "recvWindow": self._recv_window,
        }
        if extra:
            params.update(extra)
        params["signature"] = self._sign(params)
        return params

    # ─── Headers ──────────────────────────────────────────────────────────────

    def _headers(self) -> dict:
        return {"X-MBX-APIKEY": self._api_key}

    # ─── Leverage ─────────────────────────────────────────────────────────────

    async def set_leverage(
        self, account_id: str, symbol: str, leverage: int
    ) -> LeverageResult:
        params = self._signed_request_params({
            "symbol": symbol,
            "leverage": leverage,
        })
        url = f"{self._rest_base}/fapi/v1/leverage"
        resp = await self._http.post(url, data=params, headers=self._headers())
        self._check_response(resp)
        data = resp.json()
        logger.info("Binance leverage set symbol=%s leverage=%d", symbol, leverage)
        return LeverageResult(
            account_id=account_id,
            symbol=symbol,
            leverage=data.get("leverage", leverage),
        )

    # ─── Place Order ──────────────────────────────────────────────────────────

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
        extra = {
            "symbol": symbol,
            "side": side,
            "type": order_type,
            "quantity": str(quantity),
            "newClientOrderId": client_order_id,
        }
        if reduce_only:
            extra["reduceOnly"] = "true"

        params = self._signed_request_params(extra)
        url = f"{self._rest_base}/fapi/v1/order"
        resp = await self._http.post(url, data=params, headers=self._headers())
        self._check_response(resp)
        data = resp.json()

        return self._parse_order_response(account_id, data, reduce_only)

    # ─── Close Position ───────────────────────────────────────────────────────

    async def close_position(
        self,
        account_id: str,
        client_order_id: str,
        symbol: str,
        quantity: Decimal,
    ) -> OrderResult:
        extra = {
            "symbol": symbol,
            "side": "SELL",  # will be determined by reduceOnly
            "type": "MARKET",
            "quantity": str(quantity),
            "newClientOrderId": client_order_id,
            "reduceOnly": "true",
        }
        params = self._signed_request_params(extra)
        url = f"{self._rest_base}/fapi/v1/order"
        resp = await self._http.post(url, data=params, headers=self._headers())
        self._check_response(resp)
        data = resp.json()

        return self._parse_order_response(account_id, data, reduce_only=True)

    # ─── Query ────────────────────────────────────────────────────────────────

    async def query_order(self, symbol: str, client_order_id: str) -> Optional[OrderResult]:
        """Query a live order by client_order_id."""
        params = self._signed_request_params({
            "symbol": symbol,
            "origClientOrderId": client_order_id,
        })
        url = f"{self._rest_base}/fapi/v1/order"
        resp = await self._http.get(url, params=params, headers=self._headers())
        if resp.status_code == 400:
            # Order not found
            return None
        self._check_response(resp)
        data = resp.json()
        return self._parse_order_response("", data)

    # ─── Helpers ──────────────────────────────────────────────────────────────

    def _check_response(self, resp: httpx.Response) -> None:
        if resp.status_code == 429:
            raise RuntimeError("Binance rate limit exceeded (429)")
        if resp.status_code == 418:
            raise RuntimeError("Binance IP banned (418) — stop all requests")
        if resp.status_code >= 400:
            try:
                data = resp.json()
                code = data.get("code", resp.status_code)
                msg = data.get("msg", resp.text)
            except Exception:
                code = resp.status_code
                msg = resp.text
            raise RuntimeError(f"Binance error {code}: {msg}")

    def _parse_order_response(
        self, account_id: str, data: dict, reduce_only: bool = False
    ) -> OrderResult:
        return OrderResult(
            account_id=account_id,
            account_type="live",
            client_order_id=data.get("clientOrderId", ""),
            exchange_order_id=str(data.get("orderId", "")),
            symbol=data.get("symbol", ""),
            side=data.get("side", ""),
            order_type=data.get("type", ""),
            status=data.get("status", ""),
            executed_qty=Decimal(str(data.get("executedQty", "0"))),
            avg_price=Decimal(str(data.get("avgPrice", "0"))),
            leverage=None,
            realized_pnl=Decimal(str(data.get("realizedPnl", "0"))),
            fee_amount=Decimal("0"),  # Fee not in order response
            reduce_only=reduce_only,
            created_at=datetime.now(UTC),
        )
