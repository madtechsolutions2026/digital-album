"""
Photo repository for database operations.

This module provides data access methods for photos, events, and face embeddings.
"""

import logging
from typing import Optional, List, Dict, Any
from datetime import datetime

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError
import numpy as np

from app.models import Event, Photo, FaceEmbedding
from app.exceptions import EventNotFoundError, DatabaseError


class PhotoRepository:
    """
    Repository for photo-related database operations.
    
    Handles:
    - Photo creation and retrieval
    - Face embedding storage
    - Event validation
    """
    
    def __init__(self, session: AsyncSession):
        """
        Initialize the repository with a database session.
        
        Args:
            session: Async SQLAlchemy session
        """
        self.session = session
        self.logger = logging.getLogger(__name__)
    
    async def get_event(self, event_id: int) -> Optional[Event]:
        """
        Get an event by ID.
        
        Args:
            event_id: ID of the event
            
        Returns:
            Event object if found, None otherwise
            
        Raises:
            DatabaseError: If database query fails
        """
        try:
            result = await self.session.execute(
                select(Event).where(Event.event_id == event_id)
            )
            return result.scalar_one_or_none()
            
        except SQLAlchemyError as e:
            self.logger.error(
                f"Database error getting event {event_id}: {str(e)}",
                exc_info=True,
                extra={"event_id": event_id}
            )
            raise DatabaseError(f"Failed to retrieve event: {str(e)}")
    
    async def verify_event_exists(self, event_id: int) -> None:
        """
        Verify that an event exists, raise exception if not.
        
        Args:
            event_id: ID of the event
            
        Raises:
            EventNotFoundError: If event doesn't exist
            DatabaseError: If database query fails
        """
        event = await self.get_event(event_id)
        if event is None:
            raise EventNotFoundError(event_id)
    
    async def create_photo(
        self,
        event_id: int,
        file_path: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Photo:
        """
        Create a new photo record.
        
        Args:
            event_id: ID of the event this photo belongs to
            file_path: Relative path to the stored image file
            metadata: Optional metadata dictionary (dimensions, format, etc.)
            
        Returns:
            Created Photo object with photo_id populated
            
        Raises:
            DatabaseError: If database operation fails
        """
        try:
            # Create photo record
            photo = Photo(
                event_id=event_id,
                file_path=file_path,
                photo_metadata=metadata or {},
                uploaded_at=datetime.utcnow()
            )
            
            self.session.add(photo)
            await self.session.flush()  # Get the photo_id without committing
            
            self.logger.info(
                f"Photo record created: photo_id={photo.photo_id}",
                extra={
                    "photo_id": photo.photo_id,
                    "event_id": event_id,
                    "file_path": file_path
                }
            )
            
            return photo
            
        except SQLAlchemyError as e:
            self.logger.error(
                f"Database error creating photo: {str(e)}",
                exc_info=True,
                extra={"event_id": event_id, "file_path": file_path}
            )
            raise DatabaseError(f"Failed to create photo record: {str(e)}")
    
    async def create_face_embeddings(
        self,
        photo_id: int,
        faces: List[Dict[str, Any]]
    ) -> List[FaceEmbedding]:
        """
        Create face embedding records for a photo.
        
        Args:
            photo_id: ID of the photo these faces belong to
            faces: List of face dictionaries containing:
                   - embedding_vector: 512-dimensional vector
                   - bounding_box: dict with x1, y1, x2, y2
                   - confidence_score: float
            
        Returns:
            List of created FaceEmbedding objects
            
        Raises:
            DatabaseError: If database operation fails
        """
        try:
            embeddings = []
            
            for face_data in faces:
                embedding = FaceEmbedding(
                    photo_id=photo_id,
                    embedding_vector=face_data["embedding_vector"],
                    bounding_box=face_data["bounding_box"],
                    confidence_score=face_data["confidence_score"],
                    created_at=datetime.utcnow()
                )
                self.session.add(embedding)
                embeddings.append(embedding)
            
            await self.session.flush()  # Get embedding_ids without committing
            
            self.logger.info(
                f"Created {len(embeddings)} face embedding(s) for photo {photo_id}",
                extra={"photo_id": photo_id, "num_embeddings": len(embeddings)}
            )
            
            return embeddings
            
        except SQLAlchemyError as e:
            self.logger.error(
                f"Database error creating face embeddings: {str(e)}",
                exc_info=True,
                extra={"photo_id": photo_id, "num_faces": len(faces)}
            )
            raise DatabaseError(f"Failed to create face embeddings: {str(e)}")
    
    async def get_photo_by_id(self, photo_id: int) -> Optional[Photo]:
        """
        Get a photo by ID with relationships loaded.
        
        Args:
            photo_id: ID of the photo
            
        Returns:
            Photo object if found, None otherwise
            
        Raises:
            DatabaseError: If database query fails
        """
        try:
            result = await self.session.execute(
                select(Photo).where(Photo.photo_id == photo_id)
            )
            return result.scalar_one_or_none()
            
        except SQLAlchemyError as e:
            self.logger.error(
                f"Database error getting photo {photo_id}: {str(e)}",
                exc_info=True,
                extra={"photo_id": photo_id}
            )
            raise DatabaseError(f"Failed to retrieve photo: {str(e)}")
    
    async def get_photos_by_event(
        self,
        event_id: int,
        limit: int = 100,
        offset: int = 0
    ) -> List[Photo]:
        """
        Get photos for an event with pagination.
        
        Args:
            event_id: ID of the event
            limit: Maximum number of photos to return
            offset: Number of photos to skip
            
        Returns:
            List of Photo objects
            
        Raises:
            DatabaseError: If database query fails
        """
        try:
            result = await self.session.execute(
                select(Photo)
                .where(Photo.event_id == event_id)
                .order_by(Photo.uploaded_at.desc())
                .limit(limit)
                .offset(offset)
            )
            return list(result.scalars().all())
            
        except SQLAlchemyError as e:
            self.logger.error(
                f"Database error getting photos for event {event_id}: {str(e)}",
                exc_info=True,
                extra={"event_id": event_id}
            )
            raise DatabaseError(f"Failed to retrieve photos: {str(e)}")
    
    async def delete_photo(self, photo_id: int) -> bool:
        """
        Delete a photo and its associated face embeddings (cascade).
        
        Args:
            photo_id: ID of the photo to delete
            
        Returns:
            True if photo was deleted, False if not found
            
        Raises:
            DatabaseError: If database operation fails
        """
        try:
            photo = await self.get_photo_by_id(photo_id)
            if photo is None:
                return False
            
            await self.session.delete(photo)
            await self.session.flush()
            
            self.logger.info(
                f"Photo deleted: photo_id={photo_id}",
                extra={"photo_id": photo_id}
            )
            
            return True
            
        except SQLAlchemyError as e:
            self.logger.error(
                f"Database error deleting photo {photo_id}: {str(e)}",
                exc_info=True,
                extra={"photo_id": photo_id}
            )
            raise DatabaseError(f"Failed to delete photo: {str(e)}")
    
    async def search_similar_faces(
        self,
        event_id: int,
        query_embedding: np.ndarray,
        threshold: float = 0.6,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Search for similar faces using pgvector cosine similarity.
        
        Uses the cosine distance operator from pgvector to find faces
        similar to the query embedding. Returns results above the
        similarity threshold, ordered by similarity score (highest first).
        
        Args:
            event_id: ID of the event to search within
            query_embedding: 512-dimensional face embedding to search for
            threshold: Minimum similarity threshold (0.0 to 1.0)
            limit: Maximum number of results to return (default 100)
            
        Returns:
            List of dictionaries containing:
            - photo_id: ID of the photo
            - file_path: Path to the photo file
            - bounding_box: Face bounding box coordinates
            - similarity_score: Similarity score (0.0 to 1.0)
            - embedding_id: ID of the face embedding
            
        Raises:
            DatabaseError: If database query fails
        """
        try:
            # Convert numpy array to list for pgvector
            query_vector = query_embedding.tolist()
            
            # Build query using pgvector's cosine distance operator
            # Cosine similarity = 1 - cosine_distance
            # We use the <=> operator which computes cosine distance
            similarity_expr = 1 - FaceEmbedding.embedding_vector.cosine_distance(query_vector)
            
            # Query for similar faces
            # Join FaceEmbedding with Photo to get file paths
            # Filter by event_id and similarity threshold
            query = (
                select(
                    Photo.photo_id,
                    Photo.file_path,
                    FaceEmbedding.embedding_id,
                    FaceEmbedding.bounding_box,
                    FaceEmbedding.confidence_score,
                    similarity_expr.label("similarity_score")
                )
                .join(FaceEmbedding, Photo.photo_id == FaceEmbedding.photo_id)
                .where(Photo.event_id == event_id)
                .where(similarity_expr >= threshold)
                .order_by(similarity_expr.desc())
                .limit(limit)
            )
            
            result = await self.session.execute(query)
            rows = result.all()
            
            # Convert to list of dictionaries
            matches = []
            for row in rows:
                matches.append({
                    "photo_id": row.photo_id,
                    "file_path": row.file_path,
                    "embedding_id": row.embedding_id,
                    "bounding_box": row.bounding_box,
                    "confidence_score": row.confidence_score,
                    "similarity_score": float(row.similarity_score)
                })
            
            self.logger.info(
                f"Face search found {len(matches)} matches (threshold={threshold})",
                extra={
                    "event_id": event_id,
                    "num_matches": len(matches),
                    "threshold": threshold
                }
            )
            
            return matches
            
        except SQLAlchemyError as e:
            self.logger.error(
                f"Database error searching for similar faces: {str(e)}",
                exc_info=True,
                extra={"event_id": event_id, "threshold": threshold}
            )
            raise DatabaseError(f"Failed to search for similar faces: {str(e)}")
