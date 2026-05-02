"""Initial schema — all tables for simulated trading system.

Revision ID: 001
Revises: None
Create Date: 2026-05-02
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # accounts
    op.create_table(
        "accounts",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("account_type", sa.String(), nullable=False),
        sa.Column("quote_asset", sa.String(), nullable=False, server_default="USDT"),
        sa.Column("initial_balance", sa.Numeric(), nullable=False),
        sa.Column("status", sa.String(), nullable=False, server_default="active"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_check_constraint(
        "ck_accounts_account_type",
        "accounts",
        "account_type IN ('simulated', 'live')",
    )

    # account_credentials
    op.create_table(
        "account_credentials",
        sa.Column("account_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("accounts.id"), primary_key=True),
        sa.Column("api_key", sa.Text(), nullable=False),
        sa.Column("encrypted_api_secret", sa.Text(), nullable=False),
        sa.Column("key_provider", sa.String(), nullable=False, server_default="local_encrypted"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    # balances (simulated only)
    op.create_table(
        "balances",
        sa.Column("account_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("accounts.id"), primary_key=True),
        sa.Column("asset", sa.Text(), primary_key=True),
        sa.Column("wallet_balance", sa.Numeric(), nullable=False),
        sa.Column("available_balance", sa.Numeric(), nullable=False),
        sa.Column("margin_balance", sa.Numeric(), nullable=False),
        sa.Column("unrealized_pnl", sa.Numeric(), nullable=False, server_default="0"),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    # positions (simulated only)
    op.create_table(
        "positions",
        sa.Column("account_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("accounts.id"), primary_key=True),
        sa.Column("symbol", sa.Text(), primary_key=True),
        sa.Column("position_side", sa.String(), primary_key=True, server_default="BOTH"),
        sa.Column("quantity", sa.Numeric(), nullable=False, server_default="0"),
        sa.Column("entry_price", sa.Numeric(), nullable=False, server_default="0"),
        sa.Column("breakeven_price", sa.Numeric(), nullable=False, server_default="0"),
        sa.Column("leverage", sa.Integer(), nullable=False),
        sa.Column("margin_type", sa.String(), nullable=False),
        sa.Column("isolated_margin", sa.Numeric(), nullable=False, server_default="0"),
        sa.Column("unrealized_pnl", sa.Numeric(), nullable=False, server_default="0"),
        sa.Column("realized_pnl", sa.Numeric(), nullable=False, server_default="0"),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_check_constraint(
        "ck_positions_margin_type",
        "positions",
        "margin_type IN ('cross', 'isolated')",
    )

    # orders (simulated only)
    op.create_table(
        "orders",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("account_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("accounts.id"), nullable=False),
        sa.Column("symbol", sa.Text(), nullable=False),
        sa.Column("client_order_id", sa.Text(), nullable=False),
        sa.Column("exchange_order_id", sa.Text(), nullable=True),
        sa.Column("side", sa.String(), nullable=False),
        sa.Column("position_side", sa.String(), nullable=False, server_default="BOTH"),
        sa.Column("type", sa.String(), nullable=False),
        sa.Column("time_in_force", sa.String(), nullable=True),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("orig_qty", sa.Numeric(), nullable=False),
        sa.Column("executed_qty", sa.Numeric(), nullable=False, server_default="0"),
        sa.Column("requested_leverage", sa.Integer(), nullable=True),
        sa.Column("price", sa.Numeric(), nullable=True),
        sa.Column("stop_price", sa.Numeric(), nullable=True),
        sa.Column("avg_price", sa.Numeric(), nullable=False, server_default="0"),
        sa.Column("reduce_only", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("close_position", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("working_type", sa.String(), nullable=False, server_default="MARK_PRICE"),
        sa.Column("raw_request", postgresql.JSONB(), nullable=False),
        sa.Column("raw_response", postgresql.JSONB(), nullable=True),
        sa.Column("error_code", sa.Text(), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_check_constraint("ck_orders_side", "orders", "side IN ('BUY', 'SELL')")
    op.create_check_constraint("ck_orders_type", "orders", "type IN ('MARKET')")
    op.create_unique_constraint("uq_orders_account_client", "orders", ["account_id", "client_order_id"])
    op.create_index("idx_orders_account_symbol_status", "orders", ["account_id", "symbol", "status"])

    # fills (simulated only)
    op.create_table(
        "fills",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("order_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("orders.id"), nullable=False),
        sa.Column("account_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("accounts.id"), nullable=False),
        sa.Column("symbol", sa.Text(), nullable=False),
        sa.Column("side", sa.String(), nullable=False),
        sa.Column("price", sa.Numeric(), nullable=False),
        sa.Column("quantity", sa.Numeric(), nullable=False),
        sa.Column("quote_quantity", sa.Numeric(), nullable=False),
        sa.Column("fee_asset", sa.Text(), nullable=False),
        sa.Column("fee_amount", sa.Numeric(), nullable=False),
        sa.Column("realized_pnl", sa.Numeric(), nullable=False, server_default="0"),
        sa.Column("liquidity", sa.String(), nullable=False),
        sa.Column("trade_time_ms", sa.BigInteger(), nullable=False),
        sa.Column("raw_payload", postgresql.JSONB(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_check_constraint("ck_fills_liquidity", "fills", "liquidity IN ('maker', 'taker')")
    op.create_index("idx_fills_account_symbol_time", "fills", ["account_id", "symbol", "trade_time_ms"])

    # ledger_entries (simulated only)
    op.create_table(
        "ledger_entries",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("account_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("accounts.id"), nullable=False),
        sa.Column("asset", sa.Text(), nullable=False),
        sa.Column("event_type", sa.Text(), nullable=False),
        sa.Column("amount", sa.Numeric(), nullable=False),
        sa.Column("balance_after", sa.Numeric(), nullable=False),
        sa.Column("order_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("orders.id"), nullable=True),
        sa.Column("fill_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("fills.id"), nullable=True),
        sa.Column("symbol", sa.Text(), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("event_time_ms", sa.BigInteger(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("idx_ledger_account_asset_time", "ledger_entries", ["account_id", "asset", "event_time_ms"])

    # strategy_runs
    op.create_table(
        "strategy_runs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("account_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("accounts.id"), nullable=False),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("config", postgresql.JSONB(), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("stopped_at", sa.DateTime(timezone=True), nullable=True),
    )

    # system_events
    op.create_table(
        "system_events",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("level", sa.String(), nullable=False),
        sa.Column("component", sa.Text(), nullable=False),
        sa.Column("event_type", sa.Text(), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("context", postgresql.JSONB(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table("system_events")
    op.drop_table("strategy_runs")
    op.drop_index("idx_ledger_account_asset_time", "ledger_entries")
    op.drop_table("ledger_entries")
    op.drop_index("idx_fills_account_symbol_time", "fills")
    op.drop_table("fills")
    op.drop_index("idx_orders_account_symbol_status", "orders")
    op.drop_constraint("uq_orders_account_client", "orders")
    op.drop_table("orders")
    op.drop_table("positions")
    op.drop_table("balances")
    op.drop_table("account_credentials")
    op.drop_table("accounts")
