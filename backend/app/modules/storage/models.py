import uuid
from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import String, Float, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base

class StorageReading(Base):
    __tablename__ = "storage_readings"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    item_id: Mapped[str] = mapped_column(
        String, index=True, nullable=False
    )
    warehouse_zone: Mapped[str] = mapped_column(
        String, nullable=False
    )
    temperature: Mapped[float] = mapped_column(
        Float, nullable=False
    )
    humidity: Mapped[float] = mapped_column(
        Float, nullable=False
    )
    air_circulation: Mapped[str] = mapped_column(
        String, default="Medium", nullable=False
    )
    light_exposure: Mapped[str] = mapped_column(
        String, default="Low", nullable=False
    )
    recorded_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc), nullable=False
    )
