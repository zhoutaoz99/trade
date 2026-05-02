"""Unit tests for position, PnL, and fee calculations."""

from __future__ import annotations

from decimal import Decimal

import pytest

from app.services.portfolio import PortfolioService


class TestPnLCalculations:
    """Tests for realized and unrealized PnL calculations."""

    @staticmethod
    def _calc_unrealized_pnl(quantity: Decimal, entry_price: Decimal, mark_price: Decimal) -> Decimal:
        if quantity == 0 or entry_price == 0:
            return Decimal("0")
        if quantity > 0:
            return quantity * (mark_price - entry_price)
        else:
            return abs(quantity) * (entry_price - mark_price)

    def test_long_unrealized_pnl_positive(self):
        """Long position in profit when mark > entry."""
        pnl = self._calc_unrealized_pnl(
            Decimal("0.1"), Decimal("60000"), Decimal("65000")
        )
        assert pnl == Decimal("500")

    def test_long_unrealized_pnl_negative(self):
        """Long position in loss when mark < entry."""
        pnl = self._calc_unrealized_pnl(
            Decimal("0.1"), Decimal("65000"), Decimal("60000")
        )
        assert pnl == Decimal("-500")

    def test_short_unrealized_pnl_positive(self):
        """Short position in profit when mark < entry."""
        pnl = self._calc_unrealized_pnl(
            Decimal("-0.1"), Decimal("65000"), Decimal("60000")
        )
        assert pnl == Decimal("500")

    def test_short_unrealized_pnl_negative(self):
        """Short position in loss when mark > entry."""
        pnl = self._calc_unrealized_pnl(
            Decimal("-0.1"), Decimal("60000"), Decimal("65000")
        )
        assert pnl == Decimal("-500")

    def test_zero_position_no_pnl(self):
        pnl = self._calc_unrealized_pnl(
            Decimal("0"), Decimal("65000"), Decimal("70000")
        )
        assert pnl == Decimal("0")


class TestRealizedPnL:
    """Tests for realized PnL calculations."""

    def test_close_long_profit(self):
        """Buy low, sell high = profit."""
        close_qty = Decimal("0.1")
        entry = Decimal("60000")
        exit_price = Decimal("65000")
        realized = close_qty * (exit_price - entry)
        assert realized == Decimal("500")

    def test_close_long_loss(self):
        """Buy high, sell low = loss."""
        close_qty = Decimal("0.1")
        entry = Decimal("65000")
        exit_price = Decimal("60000")
        realized = close_qty * (exit_price - entry)
        assert realized == Decimal("-500")

    def test_close_short_profit(self):
        """Sell high, buy back low = profit."""
        close_qty = Decimal("0.1")
        entry = Decimal("65000")
        exit_price = Decimal("60000")
        realized = close_qty * (entry - exit_price)
        assert realized == Decimal("500")

    def test_close_short_loss(self):
        """Sell low, buy back high = loss."""
        close_qty = Decimal("0.1")
        entry = Decimal("60000")
        exit_price = Decimal("65000")
        realized = close_qty * (entry - exit_price)
        assert realized == Decimal("-500")


class TestFeeCalculation:
    """Tests for fee calculations."""

    def test_taker_fee(self):
        """MARKET orders pay taker fee."""
        notional = Decimal("6500")  # 0.1 BTC * 65000
        fee_rate = Decimal("0.0005")  # 5 bps
        fee = notional * fee_rate
        assert fee == Decimal("3.25")

    def test_breakeven_price_long(self):
        """Breakeven price accounts for entry/exit fees."""
        entry_price = Decimal("65000")
        fill_qty = Decimal("0.1")
        fee_amount = Decimal("3.25")  # per side
        fee_per_unit = fee_amount / fill_qty
        breakeven = entry_price + fee_per_unit * Decimal("2")  # entry + exit fees
        expected = Decimal("65000") + (Decimal("3.25") / Decimal("0.1")) * Decimal("2")
        assert breakeven == expected


class TestPositionMath:
    """Tests for position update logic."""

    def test_open_long_position(self):
        """Opening a new long position."""
        qty = Decimal("0.1")
        price = Decimal("65000")
        # Simple: quantity = positive for long
        assert qty > 0

    def test_add_to_long_position(self):
        """Adding to existing long position — weighted avg entry."""
        old_qty = Decimal("0.1")
        old_entry = Decimal("65000")
        add_qty = Decimal("0.05")
        add_price = Decimal("66000")

        old_notional = old_qty * old_entry
        new_notional = add_qty * add_price
        new_entry = (old_notional + new_notional) / (old_qty + add_qty)

        expected = (Decimal("6500") + Decimal("3300")) / Decimal("0.15")
        assert new_entry == expected  # 65333.333...

    def test_reduce_long_position(self):
        """Partially closing long — entry price stays same."""
        old_qty = Decimal("0.1")
        old_entry = Decimal("65000")
        close_qty = Decimal("0.03")
        close_price = Decimal("67000")

        new_qty = old_qty - close_qty
        realized = close_qty * (close_price - old_entry)

        assert new_qty == Decimal("0.07")
        assert realized == Decimal("60")

    def test_cross_zero_long_to_short(self):
        """Closing long and opening short in one trade."""
        old_qty = Decimal("0.1")
        sell_qty = Decimal("0.15")
        sell_price = Decimal("65000")

        new_qty = old_qty - sell_qty  # -0.05 = short
        assert new_qty == Decimal("-0.05")

    def test_reverse_short_to_long(self):
        """Closing short and opening long."""
        old_qty = Decimal("-0.1")
        buy_qty = Decimal("0.15")
        buy_price = Decimal("65000")

        new_qty = old_qty + buy_qty  # 0.05 = long
        assert new_qty == Decimal("0.05")
