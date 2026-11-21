"""
GuestMatch model representing face matches between a registered guest and wedding photos.
"""

from datetime import datetime
from typing import TYPE_CHECKING, Optional, Dict, Any
from sqlalchemy import Integer, Float, String, DateTime, ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base

if TYPE_CHECKING:
    from app.models.guest import Guest
    from app.models.photo import Photo


class GuestMatch(Base):
    """
    GuestMatch model representing a candidate or confirmed face match.
    """
    __tablename__ = "guest_matches"

    match_id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
        index=True,
    )

    event_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("events.event_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    guest_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("guests.guest_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    photo_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("photos.photo_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    similarity: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        comment="Face similarity percentage (0.0 to 100.0 from AWS Rekognition)",
    )

    confidence: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True,
        comment="Detection confidence score",
    )

    status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="pending_review",
        index=True,
        comment="Status: pending_review (uncertain), confirmed (auto or approved), rejected",
    )

    bounding_box: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSON,
        nullable=True,
        comment="Bounding box of the face in the target photo",
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow,
    )

    reviewed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # Relationships
    guest: Mapped["Guest"] = relationship(
        "Guest",
        back_populates="matches",
        lazy="selectin",
    )

    photo: Mapped["Photo"] = relationship(
        "Photo",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return f"<GuestMatch(match_id={self.match_id}, guest_id={self.guest_id}, photo_id={self.photo_id}, sim={self.similarity}, status='{self.status}')>"
