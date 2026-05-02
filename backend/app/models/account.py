"""Account model."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy import CheckConstraint, DateTime, Numeric, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Account(Base):
    __tablename__ = "accounts"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(Text, nullable=False)
    account_type: Mapped[str] = mapped_column(
        String, CheckConstraint("account_type IN ('simulated', 'live')"), nullable=False
    )
    quote_asset: Mapped[str] = mapped_column(String, nullable=False, default="USDT")
    initial_balance: Mapped[float] = mapped_column(Numeric, nullable=False)
    status: Mapped[str] = mapped_column(String, nullable=False, default="active")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
    )

    balances: Mapped[list["Balance"]] = relationship(
        "Balance", back_populates="account", lazy="selectin"
    )
    positions: Mapped[list["Position"]] = relationship(
        "Position", back_populates="account", lazy="selectin"
    )
    orders: Mapped[list["Order"]] = relationship(
        "Order", back_populates="account", lazy="selectin"
    )
