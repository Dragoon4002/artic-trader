"""User ORM model — wallet-identified."""
import uuid
from datetime import datetime, timezone
from sqlalchemy import String, DateTime, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..base import Base


class User(Base):
    __tablename__ = "users"
    __table_args__ = (
        UniqueConstraint("wallet_address", "wallet_chain", name="uq_users_wallet"),
    )

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    wallet_address: Mapped[str] = mapped_column(String, nullable=False)
    wallet_chain: Mapped[str] = mapped_column(String, nullable=False)
    init_username: Mapped[str | None] = mapped_column(String, nullable=True)
    init_username_resolved_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    api_key_hash: Mapped[str | None] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    agents = relationship("Agent", back_populates="user", cascade="all, delete-orphan")
    secrets = relationship("UserSecret", back_populates="user", cascade="all, delete-orphan")
    session_keys = relationship(
        "AuthSessionKey", back_populates="user", cascade="all, delete-orphan"
    )
    vm = relationship(
        "UserVM",
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan",
    )
