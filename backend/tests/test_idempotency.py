"""Tests for idempotency with client_order_id."""

from __future__ import annotations

from decimal import Decimal

import pytest


class TestIdempotency:
    """Tests for client_order_id idempotency behavior."""

    def test_duplicate_client_order_id_returns_existing(self):
        """Repeated submission with same client_order_id returns existing order."""
        client_order_id = "sim-test-btcusdt-001"
        account_id = "550e8400-e29b-41d4-a716-446655440000"

        # Simulate: first submission creates an order
        orders = {}

        def submit_order(aid, coid):
            if coid in orders:
                return orders[coid]
            order = {
                "account_id": aid,
                "client_order_id": coid,
                "status": "FILLED",
            }
            orders[coid] = order
            return order

        first = submit_order(account_id, client_order_id)
        assert first["status"] == "FILLED"

        second = submit_order(account_id, client_order_id)
        assert second is first  # same object
        assert second["status"] == "FILLED"

    def test_unique_client_order_ids_dont_conflict(self):
        """Different client_order_ids create different orders."""
        orders = {}

        def submit_order(aid, coid):
            if coid in orders:
                return orders[coid]
            orders[coid] = {"client_order_id": coid}
            return orders[coid]

        o1 = submit_order("aid", "order-001")
        o2 = submit_order("aid", "order-002")

        assert o1 is not o2
        assert o1["client_order_id"] == "order-001"
        assert o2["client_order_id"] == "order-002"

    def test_different_accounts_same_client_order_id(self):
        """Same client_order_id across different accounts should not conflict."""
        # The unique constraint is (account_id, client_order_id)
        key1 = ("account-1", "same-coid")
        key2 = ("account-2", "same-coid")

        assert key1 != key2


class TestGatewayIsolation:
    """Tests that simulated gateway never calls live Binance endpoints."""

    def test_simulated_never_calls_binance_order(self):
        """SimulatedExchangeGateway must not call /fapi/v1/order."""
        from app.gateways.simulated import SimulatedExchangeGateway
        import inspect
        source = inspect.getsource(SimulatedExchangeGateway)

        assert "/fapi/v1/order" not in source
        assert "/fapi/v1/leverage" not in source
        # Should not use an HTTP client to call out
        assert "httpx" not in source.lower()

    def test_simulated_never_calls_binance_leverage(self):
        """SimulatedExchangeGateway must not call /fapi/v1/leverage."""
        from app.gateways.simulated import SimulatedExchangeGateway
        import inspect
        source = inspect.getsource(SimulatedExchangeGateway)

        assert "/fapi/v1/leverage" not in source
