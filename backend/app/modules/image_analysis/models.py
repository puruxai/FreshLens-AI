import uuid
from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import String, Float, Boolean, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base

class ImageAnalysis(Base):
    __tablename__ = "image_analyses"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    item_id: Mapped[str] = mapped_column(
        String, index=True, nullable=False
    )
    filename: Mapped[str] = mapped_column(
        String, nullable=False
    )
    file_url: Mapped[str] = mapped_column(
        String, nullable=False
    )
    freshness_score: Mapped[float] = mapped_column(
        Float, default=100.0, nullable=False
    )
    color_degradation: Mapped[float] = mapped_column(
        Float, default=0.0, nullable=False
    )
    texture_roughness: Mapped[float] = mapped_column(
        Float, default=0.0, nullable=False
    )
    mold_detected: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False
    )
    mold_confidence: Mapped[float] = mapped_column(
        Float, default=0.0, nullable=False
    )
    bruising_detected: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False
    )
    bruising_confidence: Mapped[float] = mapped_column(
        Float, default=0.0, nullable=False
    )
    damage_detected: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False
    )
    damage_confidence: Mapped[float] = mapped_column(
        Float, default=0.0, nullable=False
    )
    classification_label: Mapped[str] = mapped_column(
        String, default="unknown/uncertain", nullable=False
    )
    status_message: Mapped[str] = mapped_column(
        String, default="Normal classification", nullable=False
    )
    analyzed_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc), nullable=False
    )
