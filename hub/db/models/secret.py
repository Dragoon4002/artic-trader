"""UserSecret + AgentSecretOverride ORM models."""

import uuid

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..base import Base


class UserSecret(Base):
    __tablename__ = "user_secrets"

    id: Mapped[str] = mapped_column(
        String, primary_key=True, default=lambda: str(uuid.uuid4())
    )
    user_id: Mapped[str] = mapped_column(String, ForeignKey("users.id"), nullable=False)
    key_name: Mapped[str] = mapped_column(String, nullable=False)
    encrypted_value: Mapped[str] = mapped_column(Text, nullable=False)

    user = relationship("User", back_populates="secrets")


class AgentSecretOverride(Base):
    __tablename__ = "agent_secret_overrides"

    id: Mapped[str] = mapped_column(
        String, primary_key=True, default=lambda: str(uuid.uuid4())
    )
    agent_id: Mapped[str] = mapped_column(
        String, ForeignKey("agents.id"), nullable=False
    )
    key_name: Mapped[str] = mapped_column(String, nullable=False)
    encrypted_value: Mapped[str] = mapped_column(Text, nullable=False)

    agent = relationship("Agent", back_populates="secret_overrides")
