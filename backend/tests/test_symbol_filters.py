"""Unit tests for symbol filter validation."""

from __future__ import annotations

from decimal import Decimal

import pytest
from unittest.mock import AsyncMock, patch

from app.services.risk import RiskService
from app.services.market_data import SymbolInfo, SymbolFilter, BookTicker


class TestSymbolFilterValidation:
    """Tests for symbol-level filter validation in RiskService."""

    @pytest.fixture
    def risk_svc(self, db_session):
        return RiskService(db_session)

    @pytest.fixture
    def mock_symbol_info(self):
        return SymbolInfo(
            symbol="BTCUSDT",
            base_asset="BTC",
            quote_asset="USDT",
            price_precision=2,
            quantity_precision=3,
            filters=SymbolFilter(
                tick_size=Decimal("0.01"),
                step_size=Decimal("0.001"),
                min_qty=Decimal("0.001"),
                min_notional=Decimal("5"),
            ),
            order_types=["MARKET", "LIMIT"],
            status="TRADING",
        )

    @pytest.mark.asyncio
    async def test_valid_quantity_passes(self, risk_svc, mock_symbol_info):
        with patch(
            "app.services.risk.market_data_service.get_symbol",
            AsyncMock(return_value=mock_symbol_info),
        ), patch(
            "app.services.risk.market_data_service.get_latest_book_ticker",
            AsyncMock(return_value=BookTicker(
                symbol="BTCUSDT",
                bid_price=Decimal("65000"),
                bid_qty=Decimal("1"),
                ask_price=Decimal("65001"),
                ask_qty=Decimal("1"),
            )),
        ):
            result = await risk_svc.validate_symbol_filters(
                "BTCUSDT", Decimal("0.001"), 1
            )
            assert result.passed is True

    @pytest.mark.asyncio
    async def test_quantity_below_min_qty_fails(self, risk_svc, mock_symbol_info):
        with patch(
            "app.services.risk.market_data_service.get_symbol",
            AsyncMock(return_value=mock_symbol_info),
        ):
            result = await risk_svc.validate_symbol_filters(
                "BTCUSDT", Decimal("0.0001"), 1
            )
            assert result.passed is False
            # 0.0001 fails step_size before reaching min_qty check
            assert "step size" in result.reason.lower() or "below min" in result.reason.lower()

    @pytest.mark.asyncio
    async def test_quantity_step_size_mismatch_fails(self, risk_svc, mock_symbol_info):
        with patch(
            "app.services.risk.market_data_service.get_symbol",
            AsyncMock(return_value=mock_symbol_info),
        ):
            result = await risk_svc.validate_symbol_filters(
                "BTCUSDT", Decimal("0.0015"), 1
            )
            assert result.passed is False
            assert "step size" in result.reason.lower()

    @pytest.mark.asyncio
    async def test_unknown_symbol_fails(self, risk_svc):
        with patch(
            "app.services.risk.market_data_service.get_symbol",
            AsyncMock(side_effect=ValueError("Unknown symbol: XXXUSDT")),
        ):
            result = await risk_svc.validate_symbol_filters(
                "XXXUSDT", Decimal("0.001"), 1
            )
            assert result.passed is False
            assert "Unknown symbol" in result.reason

    @pytest.mark.asyncio
    async def test_unsupported_order_type_fails(self, risk_svc, mock_symbol_info):
        mock_symbol_info.order_types = ["LIMIT"]
        with patch(
            "app.services.risk.market_data_service.get_symbol",
            AsyncMock(return_value=mock_symbol_info),
        ):
            result = await risk_svc.validate_symbol_filters(
                "BTCUSDT", Decimal("0.001"), 1
            )
            assert result.passed is False
            assert "not supported" in result.reason.lower()


class TestRiskOrderChecks:
    """Tests for risk-level order checks."""

    @pytest.fixture
    def risk_svc(self, db_session):
        return RiskService(db_session)

    @pytest.fixture
    def _mock_book_ticker(self):
        return patch(
            "app.services.risk.market_data_service.get_latest_book_ticker",
            AsyncMock(return_value=BookTicker(
                symbol="BTCUSDT",
                bid_price=Decimal("65000"),
                bid_qty=Decimal("1"),
                ask_price=Decimal("65001"),
                ask_qty=Decimal("1"),
            )),
        )

    @pytest.mark.asyncio
    async def test_leverage_exceeds_max_fails(self, risk_svc, _mock_book_ticker):
        with _mock_book_ticker:
            result = await risk_svc.check_order(
                symbol="BTCUSDT",
                side="BUY",
                quantity=Decimal("0.001"),
                leverage=999,
            )
            assert result.passed is False
            assert "Leverage" in result.reason

    @pytest.mark.asyncio
    async def test_order_notional_exceeds_max_fails(self, risk_svc, _mock_book_ticker):
        with _mock_book_ticker:
            result = await risk_svc.check_order(
                symbol="BTCUSDT",
                side="BUY",
                quantity=Decimal("100"),
                leverage=5,
            )
            assert result.passed is False
            assert "notional" in result.reason.lower()

    @pytest.mark.asyncio
    async def test_insufficient_margin_fails(self, risk_svc, _mock_book_ticker):
        with _mock_book_ticker:
            # 0.1 BTC * 65001 = 6500.1 notional, margin = 1300.02 > 100 available
            result = await risk_svc.check_order(
                symbol="BTCUSDT",
                side="BUY",
                quantity=Decimal("0.1"),
                leverage=5,
                available_balance=Decimal("100"),
            )
            assert result.passed is False
            assert "margin" in result.reason.lower()

    @pytest.mark.asyncio
    async def test_reduce_only_wrong_direction_fails(self, risk_svc, _mock_book_ticker):
        with _mock_book_ticker:
            result = await risk_svc.check_order(
                symbol="BTCUSDT",
                side="BUY",
                quantity=Decimal("0.001"),
                leverage=5,
                reduce_only=True,
                current_position_qty=Decimal("0.01"),
            )
            assert result.passed is False
            assert "Reduce-only" in result.reason

    @pytest.mark.asyncio
    async def test_reduce_only_exceeds_position_fails(self, risk_svc, _mock_book_ticker):
        with _mock_book_ticker:
            # 0.05 * 65000 = 3250 notional (under 10k limit) but reduce qty exceeds position
            result = await risk_svc.check_order(
                symbol="BTCUSDT",
                side="SELL",
                quantity=Decimal("0.05"),
                leverage=5,
                reduce_only=True,
                current_position_qty=Decimal("0.001"),
            )
            assert result.passed is False
            assert "exceeds position" in result.reason.lower()
