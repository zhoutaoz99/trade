"""Position model — simulated accounts only."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    Uuid,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Position(Base):
    __tablename__ = "positions"

    account_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("accounts.id"), primary_key=True
    )
    symbol: Mapped[str] = mapped_column(Text, primary_key=True)
    position_side: Mapped[str] = mapped_column(
        String, primary_key=True, default="BOTH"
    )
    quantity: Mapped[float] = mapped_column(Numeric, nullable=False, default=0)
    entry_price: Mapped[float] = mapped_column(Numeric, nullable=False, default=0)
    breakeven_price: Mapped[float] = mapped_column(Numeric, nullable=False, default=0)
    leverage: Mapped[int] = mapped_column(Integer, nullable=False)
    margin_type: Mapped[str] = mapped_column(
        String,
        CheckConstraint("margin_type IN ('cross', 'isolated')"),
        nullable=False,
    )
    isolated_margin: Mapped[float] = mapped_column(Numeric, nullable=False, default=0)
    unrealized_pnl: Mapped[float] = mapped_column(Numeric, nullable=False, default=0)
    realized_pnl: Mapped[float] = mapped_column(Numeric, nullable=False, default=0)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
    )

    account: Mapped["Account"] = relationship("Account", back_populates="positions")
