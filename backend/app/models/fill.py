"""Fill (trade) model — simulated accounts only."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy import BigInteger, CheckConstraint, DateTime, ForeignKey, JSON, Numeric, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Fill(Base):
    __tablename__ = "fills"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    order_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("orders.id"), nullable=False, index=True
    )
    account_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("accounts.id"), nullable=False, index=True
    )
    symbol: Mapped[str] = mapped_column(Text, nullable=False)
    side: Mapped[str] = mapped_column(String, nullable=False)
    price: Mapped[float] = mapped_column(Numeric, nullable=False)
    quantity: Mapped[float] = mapped_column(Numeric, nullable=False)
    quote_quantity: Mapped[float] = mapped_column(Numeric, nullable=False)
    fee_asset: Mapped[str] = mapped_column(Text, nullable=False)
    fee_amount: Mapped[float] = mapped_column(Numeric, nullable=False)
    realized_pnl: Mapped[float] = mapped_column(Numeric, nullable=False, default=0)
    liquidity: Mapped[str] = mapped_column(
        String, CheckConstraint("liquidity IN ('maker', 'taker')"), nullable=False
    )
    trade_time_ms: Mapped[int] = mapped_column(BigInteger, nullable=False)
    raw_payload: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC)
    )

    order: Mapped["Order"] = relationship("Order", back_populates="fills")
