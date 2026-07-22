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
