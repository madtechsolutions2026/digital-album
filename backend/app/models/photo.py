"""
Photo model for uploaded images at events.

Photos represent individual image files uploaded to events, with metadata
and relationships to detected face embeddings.
"""

from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Integer, String, DateTime, ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.event import Event
    from app.models.face_embedding import FaceEmbedding


class Photo(Base):
    """
    Photo model representing an uploaded image file.
    
    Attributes:
        photo_id: Primary key, auto-incrementing integer
        event_id: Foreign key to events table
        file_path: Relative path to the stored image file
        metadata: JSONB field for additional metadata (dimensions, format, etc.)
        uploaded_at: Timestamp when photo was uploaded
        event: Relationship to parent Event
        face_embeddings: Relationship to detected FaceEmbedding records
    """
    
    __tablename__ = "photos"
    
    # Primary key
    photo_id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
        index=True,
    )
    
    # Foreign key to event
    event_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("events.event_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Foreign key to the event this photo belongs to",
    )
    
    # File information
    file_path: Mapped[str] = mapped_column(
        String(512),
        nullable=False,
        unique=True,
        comment="Relative path to the stored image file",
    )
    
    # Metadata stored as JSONB for flexibility
    # Can store: original_filename, width, height, format, file_size, etc.
    photo_metadata: Mapped[Optional[dict]] = mapped_column(
        JSON,
        nullable=True,
        comment="Additional metadata about the photo (dimensions, format, etc.)",
    )
    
    # Timestamp
    uploaded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow,
        index=True,
        comment="Timestamp when the photo was uploaded",
    )
    
    # Relationships
    event: Mapped["Event"] = relationship(
        "Event",
        back_populates="photos",
        lazy="selectin",
    )
    
    face_embeddings: Mapped[list["FaceEmbedding"]] = relationship(
        "FaceEmbedding",
        back_populates="photo",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    
    def __repr__(self) -> str:
        """String representation of Photo."""
        return f"<Photo(photo_id={self.photo_id}, event_id={self.event_id}, file_path='{self.file_path}')>"
