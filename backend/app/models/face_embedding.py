"""
FaceEmbedding model for storing face detection results and embeddings.

Each face embedding represents a detected face in a photo, with its 512-dimensional
embedding vector for similarity search using pgvector.
"""

from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Integer, Float, DateTime, ForeignKey, JSON, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from pgvector.sqlalchemy import Vector

from app.database import Base

if TYPE_CHECKING:
    from app.models.photo import Photo


class FaceEmbedding(Base):
    """
    FaceEmbedding model representing a detected face in a photo.
    
    Stores the normalized face embedding vector (512 dimensions from the
    configured InsightFace model pack)
    along with metadata about the face detection (bounding box, confidence score).
    
    Attributes:
        embedding_id: Primary key, auto-incrementing integer
        photo_id: Foreign key to photos table
        embedding_vector: 512-dimensional vector for face similarity search (pgvector)
        bounding_box: JSONB field storing face location {x1, y1, x2, y2}
        confidence_score: Face detection confidence score (0.0 to 1.0)
        model_name: InsightFace model pack used to generate the vector
        created_at: Timestamp when embedding was created
        photo: Relationship to parent Photo
    """
    
    __tablename__ = "face_embeddings"
    
    # Primary key
    embedding_id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
        index=True,
    )
    
    # Foreign key to photo
    photo_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("photos.photo_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Foreign key to the photo this face belongs to",
    )
    
    # Face embedding vector (512 dimensions for the configured InsightFace pack)
    # Using pgvector's Vector type for efficient similarity search
    embedding_vector: Mapped[list[float]] = mapped_column(
        Vector(512),
        nullable=False,
        comment="512-dimensional face embedding vector from InsightFace",
    )

    # Model provenance matters: buffalo_s and buffalo_l both emit 512 values
    # but those vectors are not comparable.  Keeping the pack on each row lets
    # the service re-index safely when a higher-accuracy model is selected.
    model_name: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        default="buffalo_s",
        server_default="buffalo_s",
        index=True,
        comment="InsightFace model pack used to create this embedding",
    )
    
    # Face bounding box stored as JSON: {x1, y1, x2, y2}
    # Coordinates represent pixel positions in the image
    bounding_box: Mapped[dict] = mapped_column(
        JSON,
        nullable=False,
        comment="Face bounding box coordinates {x1, y1, x2, y2}",
    )
    
    # Confidence score from face detection (0.0 to 1.0)
    confidence_score: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        comment="Face detection confidence score (0.0 to 1.0)",
    )
    
    # Timestamp
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow,
        comment="Timestamp when the embedding was created",
    )
    
    # Relationships
    photo: Mapped["Photo"] = relationship(
        "Photo",
        back_populates="face_embeddings",
        lazy="selectin",
    )
    
    def __repr__(self) -> str:
        """String representation of FaceEmbedding."""
        return (
            f"<FaceEmbedding(embedding_id={self.embedding_id}, "
            f"photo_id={self.photo_id}, model={self.model_name}, "
            f"confidence={self.confidence_score:.3f})>"
        )
