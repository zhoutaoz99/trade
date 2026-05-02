"""Encrypted API credentials for live accounts."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy import DateTime, ForeignKey, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class AccountCredential(Base):
    __tablename__ = "account_credentials"

    account_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("accounts.id"),
        primary_key=True,
    )
    api_key: Mapped[str] = mapped_column(Text, nullable=False)
    encrypted_api_secret: Mapped[str] = mapped_column(Text, nullable=False)
    key_provider: Mapped[str] = mapped_column(String, nullable=False, default="local_encrypted")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
    )

    account: Mapped["Account"] = relationship("Account", lazy="selectin")
