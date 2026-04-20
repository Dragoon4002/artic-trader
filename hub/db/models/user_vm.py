"""User VM record — one per user."""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..base import Base


class UserVM(Base):
    __tablename__ = "user_vms"

    id: Mapped[str] = mapped_column(
        String, primary_key=True, default=lambda: str(uuid.uuid4())
    )
    user_id: Mapped[str] = mapped_column(
        String, ForeignKey("users.id"), unique=True, nullable=False
    )
    provider_vm_id: Mapped[str | None] = mapped_column(String, nullable=True)
    endpoint: Mapped[str | None] = mapped_column(String, nullable=True)
    status: Mapped[str] = mapped_column(String, default="stopped", nullable=False)
    last_active_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    image_tag: Mapped[str | None] = mapped_column(String, nullable=True)
    wallet_address: Mapped[str | None] = mapped_column(String, nullable=True)
    snapshot_id: Mapped[str | None] = mapped_column(String, nullable=True)

    user = relationship("User", back_populates="vm")
