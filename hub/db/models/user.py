"""User ORM model."""

import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..base import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(
        String, primary_key=True, default=lambda: str(uuid.uuid4())
    )
    email: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String, nullable=False)
    api_key_hash: Mapped[str | None] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    secrets = relationship(
        "UserSecret", back_populates="user", cascade="all, delete-orphan"
    )
    vm = relationship(
        "UserVM", back_populates="user", cascade="all, delete-orphan", uselist=False
    )
    # Retained for deprecated-agent FK integrity; slated for removal in indexer branch.
    agents = relationship("Agent", back_populates="user", cascade="all, delete-orphan")
