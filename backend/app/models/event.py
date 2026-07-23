"""
Event model for wedding/celebration events.

Events represent individual weddings or celebrations that have associated photos.
Each event can have multiple photos uploaded to it.
"""

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Integer, String, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.photo import Photo


class Event(Base):
    """
    Event model representing a wedding or celebration.
    
    Attributes:
        event_id: Primary key, auto-incrementing integer
        name: Event name (e.g., "Smith Wedding 2024")
        event_date: Date of the event
        created_at: Timestamp when record was created
        updated_at: Timestamp when record was last updated
        photos: Relationship to associated Photo records
    """
    
    __tablename__ = "events"
    
    # Primary key
    event_id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
        index=True,
    )
    
    # Event details
    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        comment="Name of the event (e.g., 'Smith Wedding 2024')",
    )
    
    event_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        comment="Date and time of the event",
    )

    # Private access credentials - guests unlock the gallery with these
    # instead of creating an account. access_code is shown to guests
    # directly; password_hash is bcrypt, the plaintext password is only
    # ever returned once, at creation time.
    access_code: Mapped[str] = mapped_column(
        String(12),
        nullable=False,
        unique=True,
        index=True,
        comment="Unique code guests enter to access this event's gallery",
    )

    password_hash: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        comment="Bcrypt hash of the access password (plaintext shown once at creation)",
    )

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow,
        comment="Timestamp when the record was created",
    )
    
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        comment="Timestamp when the record was last updated",
    )
    
    # Relationships
    photos: Mapped[list["Photo"]] = relationship(
        "Photo",
        back_populates="event",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    
    def __repr__(self) -> str:
        """String representation of Event."""
        return f"<Event(event_id={self.event_id}, name='{self.name}', event_date={self.event_date})>"
