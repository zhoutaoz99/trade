"""Balance model — simulated accounts only."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy import DateTime, ForeignKey, Numeric, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Balance(Base):
    __tablename__ = "balances"

    account_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("accounts.id"), primary_key=True
    )
    asset: Mapped[str] = mapped_column(Text, primary_key=True)
    wallet_balance: Mapped[float] = mapped_column(Numeric, nullable=False)
    available_balance: Mapped[float] = mapped_column(Numeric, nullable=False)
    margin_balance: Mapped[float] = mapped_column(Numeric, nullable=False)
    unrealized_pnl: Mapped[float] = mapped_column(Numeric, nullable=False, default=0)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
    )

    account: Mapped["Account"] = relationship("Account", back_populates="balances")
