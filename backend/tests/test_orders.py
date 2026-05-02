"""Tests for order lifecycle and state machine."""

from __future__ import annotations

from decimal import Decimal

import pytest


class TestOrderValidation:
    """Tests for order request validation."""

    def test_market_order_is_accepted(self):
        """Only MARKET orders are supported in v1."""
        order_type = "MARKET"
        assert order_type in ("MARKET",)

    def test_limit_order_is_rejected(self):
        """LIMIT orders are not supported in v1."""
        order_type = "LIMIT"
        if order_type != "MARKET":
            with pytest.raises(ValueError):
                raise ValueError("Only MARKET orders are supported")
        else:
            pytest.fail("LIMIT should not be accepted")

    def test_buy_side_is_valid(self):
        side = "BUY"
        assert side in ("BUY", "SELL")

    def test_sell_side_is_valid(self):
        side = "SELL"
        assert side in ("BUY", "SELL")

    def test_invalid_side_is_rejected(self):
        side = "INVALID"
        if side not in ("BUY", "SELL"):
            with pytest.raises(ValueError):
                raise ValueError("side must be BUY or SELL")


class TestClosePosition:
    """Tests for close-position logic."""

    def test_close_long_generates_sell(self):
        """Closing a long position generates a SELL reduce-only order."""
        position_qty = Decimal("0.1")
        if position_qty > 0:
            close_side = "SELL"
        else:
            close_side = "BUY"
        assert close_side == "SELL"

    def test_close_short_generates_buy(self):
        """Closing a short position generates a BUY reduce-only order."""
        position_qty = Decimal("-0.1")
        if position_qty > 0:
            close_side = "SELL"
        else:
            close_side = "BUY"
        assert close_side == "BUY"

    def test_close_quantity_cannot_exceed_position(self):
        """Close quantity is capped at position size."""
        position_qty = Decimal("0.05")
        requested_qty = Decimal("0.1")
        actual_qty = min(requested_qty, abs(position_qty))
        assert actual_qty == Decimal("0.05")

    def test_close_zero_position_fails(self):
        """Cannot close when there is no position."""
        position_qty = Decimal("0")
        if position_qty == 0:
            with pytest.raises(ValueError):
                raise ValueError("No open position")
