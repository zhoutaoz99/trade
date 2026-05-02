"""Order model — simulated accounts only."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Integer,
    JSON,
    Numeric,
    String,
    Text,
    Uuid,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Order(Base):
    __tablename__ = "orders"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    account_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("accounts.id"), nullable=False, index=True
    )
    symbol: Mapped[str] = mapped_column(Text, nullable=False)
    client_order_id: Mapped[str] = mapped_column(Text, nullable=False)
    exchange_order_id: Mapped[str | None] = mapped_column(Text, nullable=True)
    side: Mapped[str] = mapped_column(
        String, CheckConstraint("side IN ('BUY', 'SELL')"), nullable=False
    )
    position_side: Mapped[str] = mapped_column(String, nullable=False, default="BOTH")
    type: Mapped[str] = mapped_column(
        String, CheckConstraint("type IN ('MARKET')"), nullable=False
    )
    time_in_force: Mapped[str | None] = mapped_column(String, nullable=True)
    status: Mapped[str] = mapped_column(String, nullable=False)
    orig_qty: Mapped[float] = mapped_column(Numeric, nullable=False)
    executed_qty: Mapped[float] = mapped_column(Numeric, nullable=False, default=0)
    requested_leverage: Mapped[int | None] = mapped_column(Integer, nullable=True)
    price: Mapped[float | None] = mapped_column(Numeric, nullable=True)
    stop_price: Mapped[float | None] = mapped_column(Numeric, nullable=True)
    avg_price: Mapped[float] = mapped_column(Numeric, nullable=False, default=0)
    reduce_only: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    close_position: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    working_type: Mapped[str] = mapped_column(String, nullable=False, default="MARK_PRICE")
    raw_request: Mapped[dict] = mapped_column(JSON, nullable=False)
    raw_response: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    error_code: Mapped[str | None] = mapped_column(Text, nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
    )

    account: Mapped["Account"] = relationship("Account", back_populates="orders")
    fills: Mapped[list["Fill"]] = relationship(
        "Fill", back_populates="order", lazy="selectin"
    )
