"""Auto-signing session keys. Public half + monotonic-nonce counter."""
import uuid
from datetime import datetime, timezone
from sqlalchemy import String, DateTime, BigInteger, ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..base import Base


class AuthSessionKey(Base):
    __tablename__ = "auth_session_keys"
    __table_args__ = (
        Index("ix_auth_session_active", "user_id", "revoked_at"),
    )

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(String, ForeignKey("users.id"), nullable=False)
    session_pub: Mapped[str] = mapped_column(String, nullable=False)
    scope: Mapped[str] = mapped_column(String, nullable=False, default="authenticated-actions")
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    last_nonce: Mapped[int] = mapped_column(BigInteger, nullable=False, default=0)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    user = relationship("User", back_populates="session_keys")
