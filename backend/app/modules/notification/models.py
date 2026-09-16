import uuid
from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import String, Float, Boolean, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base

class Notification(Base):
    __tablename__ = "notifications"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[Optional[str]] = mapped_column(
        String, index=True, nullable=True
    )
    role: Mapped[Optional[str]] = mapped_column(
        String, index=True, nullable=True
    )
    title: Mapped[str] = mapped_column(
        String, nullable=False
    )
    message: Mapped[str] = mapped_column(
        String, nullable=False
    )
    type: Mapped[str] = mapped_column(
        String, nullable=False
    )
    is_read: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc), nullable=False
    )

class NotificationPreference(Base):
    __tablename__ = "notification_preferences"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[str] = mapped_column(
        String, unique=True, index=True, nullable=False
    )
    email_enabled: Mapped[bool] = mapped_column(
        Boolean, default=True, nullable=False
    )
    push_enabled: Mapped[bool] = mapped_column(
        Boolean, default=True, nullable=False
    )
    min_freshness_threshold: Mapped[float] = mapped_column(
        Float, default=50.0, nullable=False
    )
    storage_alerts_enabled: Mapped[bool] = mapped_column(
        Boolean, default=True, nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc), nullable=False
    )
