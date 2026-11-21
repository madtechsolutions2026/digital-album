"""
Guest model for wedding attendees who register via QR code to receive their private album.
"""

from datetime import datetime
from typing import TYPE_CHECKING, List, Optional
from sqlalchemy import Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base

if TYPE_CHECKING:
    from app.models.event import Event
    from app.models.guest_match import GuestMatch


class Guest(Base):
    """
    Guest model representing a registered wedding attendee.
    """
    __tablename__ = "guests"

    guest_id: Mapped[int] = mapped_column(
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
        comment="Event this guest registered for",
    )

    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        comment="Full name of the guest",
    )

    phone: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        comment="WhatsApp phone number of the guest",
    )

    selfie_path: Mapped[Optional[str]] = mapped_column(
        String(512),
        nullable=True,
        comment="Stored path to the registration selfie",
    )

    status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="registered",
        index=True,
        comment="Status: registered, needs_review, ready_to_send, delivered",
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow,
        comment="Timestamp when guest registered",
    )

    # Relationships
    event: Mapped["Event"] = relationship(
        "Event",
        lazy="selectin",
    )

    matches: Mapped[List["GuestMatch"]] = relationship(
        "GuestMatch",
        back_populates="guest",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return f"<Guest(guest_id={self.guest_id}, name='{self.name}', phone='{self.phone}', status='{self.status}')>"
