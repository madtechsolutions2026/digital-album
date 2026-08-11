"""
Photo service for orchestrating photo upload and processing.

This module coordinates the entire photo upload workflow:
- Image validation
- File storage
- Face detection
- Embedding extraction
- Database persistence
"""

import asyncio
import logging
from typing import Callable, Dict, Any, List, Optional

from app.services.image_validator import ImageValidator
from app.services.file_storage import FileStorageService
from app.services.r2_storage import R2StorageService
from app.services.face_service import FaceRecognitionService, FaceInfo
from app.repositories.photo_repository import PhotoRepository
from app.exceptions import ValidationError, FaceDetectionError, EventNotFoundError
from app.config import get_settings


# Global semaphore bounding how many photos are validated/compressed/uploaded
# at the same time, across all requests. Without this, a large concurrent
# batch upload has no limit on how many CPU-heavy compression jobs and
# in-memory images pile up at once. Lazily created so it binds to whichever
# event loop is actually running (uvicorn's), not import time.
_upload_semaphore: Optional[asyncio.Semaphore] = None


def _get_upload_semaphore() -> asyncio.Semaphore:
    global _upload_semaphore

    if _upload_semaphore is None:
        settings = get_settings()
        _upload_semaphore = asyncio.Semaphore(settings.MAX_CONCURRENT_UPLOADS)

    return _upload_semaphore


class PhotoUploadResult:
    """
    Result of a photo upload operation.
    
    Attributes:
        photo_id: ID of the created photo record
        file_path: Relative path to the stored file
        face_count: Number of faces detected
        faces_stored: Number of face embeddings stored
        warning: Optional warning message
    """
    
    def __init__(
        self,
        photo_id: int,
        file_path: str,
        face_count: int,
        faces_stored: int,
        warning: Optional[str] = None
    ):
        self.photo_id = photo_id
        self.file_path = file_path
        self.face_count = face_count
        self.faces_stored = faces_stored
        self.warning = warning
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert result to dictionary."""
        result = {
            "photo_id": self.photo_id,
            "file_path": self.file_path,
            "face_count": self.face_count,
            "faces_stored": self.faces_stored
        }
        if self.warning:
            result["warning"] = self.warning
        return result


class PhotoService:
    """
    Service for photo upload and processing operations.
    
    Orchestrates the complete workflow:
    1. Validate image
    2. Save to disk
    3. Create photo record
    4. Detect faces
    5. Extract embeddings
    6. Store embeddings
    """
    
    def __init__(
        self,
        photo_repository: PhotoRepository,
        image_validator: ImageValidator,
        file_storage: FileStorageService,
        face_service_factory: Callable[[], FaceRecognitionService],
        r2_storage: Optional[R2StorageService] = None
    ):
        """
        Initialize the photo service with dependencies.

        Args:
            photo_repository: Repository for database operations
            image_validator: Service for image validation
            file_storage: Service for local file storage
            face_service_factory: Callable returning the face recognition
                service (e.g. get_face_service). Not called here - resolving
                it loads the InsightFace model, so it must stay lazy and only
                run on code paths that actually need face detection
                (skip_face_detection=false uploads, and searches).
            r2_storage: Optional R2 storage service
        """
        self.photo_repo = photo_repository
        self.image_validator = image_validator
        self.file_storage = file_storage
        self.r2_storage = r2_storage
        self._face_service_factory = face_service_factory
        self.logger = logging.getLogger(__name__)
        self.settings = get_settings()

    @property
    def face_service(self) -> FaceRecognitionService:
        return self._face_service_factory()
    
    async def upload_photo(
        self,
        file_content: bytes,
        filename: str,
        event_id: int,
        skip_face_detection: bool = False,
        category: Optional[str] = None
    ) -> PhotoUploadResult:
        """
        Upload and process a photo.
        
        Complete workflow:
        1. Verify event exists
        2. Validate image (size, format, dimensions)
        3. Save image to disk
        4. Create photo record in database
        5. Detect faces in image
        6. Extract embeddings
        7. Store face embeddings
        
        Args:
            file_content: Raw bytes of the uploaded file
            filename: Original filename
            event_id: ID of the event this photo belongs to
            
        Returns:
            PhotoUploadResult with photo_id, face_count, and optional warning
            
        Raises:
            ValidationError: If image validation fails
            EventNotFoundError: If event doesn't exist
            DatabaseError: If database operation fails
        """
        self.logger.info(
            f"Starting photo upload: filename={filename}, event_id={event_id}",
            extra={"uploaded_filename": filename, "event_id": event_id}
        )
        
        # Step 1: Verify event exists and get event details
        event = await self.photo_repo.get_event(event_id)
        if event is None:
            raise EventNotFoundError(event_id)
        
        # Steps 2-3 are the CPU/memory-heavy part of an upload (image decode,
        # resize, WebP compression, storage upload). Gate them with a
        # semaphore so a large concurrent batch queues cleanly instead of
        # running unbounded decode+compress work in parallel.
        async with _get_upload_semaphore():
            # Step 2: Validate and prepare image. CPU-bound (PIL decode/resize),
            # so run it off the event loop thread to allow concurrent uploads.
            image, format_str, original_size = await asyncio.to_thread(
                self.image_validator.validate_and_prepare, file_content, filename
            )

            self.logger.info(
                f"Image validated: format={format_str}, size={original_size}",
                extra={
                    "uploaded_filename": filename,
                    "format": format_str,
                    "original_size": original_size,
                    "final_size": image.size
                }
            )

            # Step 3: Save image to disk or R2. Compression (CPU-bound) and the
            # storage upload (blocking network I/O) both happen inside these
            # sync calls, so run them off the event loop thread too.
            if self.settings.STORAGE_TYPE == 'r2' and self.r2_storage:
                relative_path = await asyncio.to_thread(
                    self.r2_storage.save_image,
                    image=image,
                    event_id=event_id,
                    event_name=event.name,
                    format=format_str,
                    original_filename=filename
                )
            else:
                relative_path = await asyncio.to_thread(
                    self.file_storage.save_image,
                    image=image,
                    event_id=event_id,
                    event_name=event.name,
                    format=format_str,
                    original_filename=filename
                )
        
        # Prepare metadata for database
        metadata = {
            "original_filename": filename,
            "format": format_str,
            "original_size": {
                "width": original_size[0],
                "height": original_size[1]
            },
            "stored_size": {
                "width": image.size[0],
                "height": image.size[1]
            },
            "file_size_bytes": len(file_content),
            "category": category
        }
        
        # Step 4: Create photo record
        photo = await self.photo_repo.create_photo(
            event_id=event_id,
            file_path=relative_path,
            metadata=metadata
        )
        
        # Step 5: Detect faces and extract embeddings (optional)
        warning = None
        faces_stored = 0
        
        if skip_face_detection:
            # Skip face detection for faster upload
            warning = "Face detection skipped. Photo uploaded quickly but not searchable by face."
            self.logger.info(
                f"Skipped face detection for photo {photo.photo_id} (fast upload mode)",
                extra={
                    "photo_id": photo.photo_id,
                    "uploaded_filename": filename
                }
            )
        else:
            # Run face detection
            try:
                faces = await self.face_service.detect_faces(image)
                
                if not faces:
                    # No faces detected - this is a warning, not an error
                    warning = "No faces detected in image. Photo uploaded but not searchable by face."
                    self.logger.warning(
                        f"No faces detected in photo {photo.photo_id}",
                        extra={
                            "photo_id": photo.photo_id,
                            "uploaded_filename": filename
                        }
                    )
                else:
                    # Step 6 & 7: Store face embeddings
                    faces_stored = await self._store_face_embeddings(
                        photo_id=photo.photo_id,
                        faces=faces
                    )
                    
                    self.logger.info(
                        f"Stored {faces_stored} face embedding(s) for photo {photo.photo_id}",
                        extra={
                            "photo_id": photo.photo_id,
                            "faces_stored": faces_stored
                        }
                    )
            
            except Exception as e:
                # Face detection/embedding failure should not fail the upload
                # Log the error and continue
                warning = f"Face detection failed: {str(e)}. Photo uploaded but not searchable by face."
                self.logger.error(
                    f"Face detection failed for photo {photo.photo_id}: {str(e)}",
                    exc_info=True,
                    extra={
                        "photo_id": photo.photo_id,
                        "uploaded_filename": filename
                    }
                )
        
        # Return result
        result = PhotoUploadResult(
            photo_id=photo.photo_id,
            file_path=relative_path,
            face_count=len(faces) if 'faces' in locals() else 0,
            faces_stored=faces_stored,
            warning=warning
        )
        
        self.logger.info(
            f"Photo upload completed: photo_id={photo.photo_id}",
            extra={
                "photo_id": photo.photo_id,
                "file_path": relative_path,
                "face_count": result.face_count,
                "warning": warning
            }
        )
        
        return result
    
    async def _store_face_embeddings(
        self,
        photo_id: int,
        faces: List[FaceInfo]
    ) -> int:
        """
        Store face embeddings in the database.
        
        Args:
            photo_id: ID of the photo
            faces: List of FaceInfo objects
            
        Returns:
            Number of embeddings stored
        """
        # Convert FaceInfo objects to database format
        face_data = []
        for face in faces:
            face_data.append({
                "embedding_vector": face.embedding.tolist(),
                "bounding_box": face.bbox_as_dict(),
                "confidence_score": face.confidence
            })
        
        # Store in database
        embeddings = await self.photo_repo.create_face_embeddings(
            photo_id=photo_id,
            faces=face_data
        )
        
        return len(embeddings)
    
    async def search_faces(
        self,
        selfie_content: bytes,
        selfie_filename: str,
        event_id: int,
        threshold: float = 0.6
    ) -> Dict[str, Any]:
        """
        Search for photos containing a face similar to the selfie.
        
        Workflow:
        1. Verify event exists
        2. Validate selfie image
        3. Detect face in selfie
        4. Select largest face (primary face)
        5. Search for similar faces in event photos
        
        Args:
            selfie_content: Raw bytes of the selfie image
            selfie_filename: Original filename
            event_id: ID of the event to search in
            threshold: Minimum similarity threshold (0.0 to 1.0)
            
        Returns:
            Dictionary with:
            - matches: List of matching photos with similarity scores
            - query_face_confidence: Confidence of detected face in selfie
            - num_matches: Number of matches found
            
        Raises:
            ValidationError: If selfie validation fails or no face detected
            EventNotFoundError: If event doesn't exist
            DatabaseError: If database operation fails
        """
        self.logger.info(
            f"Starting face search: event_id={event_id}, threshold={threshold}",
            extra={
                "selfie_filename": selfie_filename,
                "event_id": event_id,
                "threshold": threshold
            }
        )
        
        # Step 1: Verify event exists
        await self.photo_repo.verify_event_exists(event_id)
        
        # Step 2: Validate selfie image
        image, _, _ = self.image_validator.validate_and_prepare(
            selfie_content, selfie_filename
        )
        
        # Step 3: Detect faces in selfie
        faces = await self.face_service.detect_faces(image)
        
        if not faces:
            raise ValidationError(
                "No face detected in selfie. Please upload a clear photo with a visible face."
            )
        
        # Step 4: Select largest face (primary face in selfie)
        primary_face = self.face_service.select_largest_face(faces)
        
        if len(faces) > 1:
            self.logger.info(
                f"Multiple faces detected ({len(faces)}), using largest face",
                extra={
                    "num_faces": len(faces),
                    "selfie_filename": selfie_filename
                }
            )
        
        # Step 5: Search for similar faces
        matches = await self.photo_repo.search_similar_faces(
            event_id=event_id,
            query_embedding=primary_face.embedding,
            threshold=threshold,
            limit=100
        )
        
        result = {
            "matches": matches,
            "query_face_confidence": primary_face.confidence,
            "num_matches": len(matches),
            "threshold_used": threshold
        }
        
        self.logger.info(
            f"Face search completed: found {len(matches)} matches",
            extra={
                "event_id": event_id,
                "num_matches": len(matches),
                "threshold": threshold,
                "query_confidence": primary_face.confidence
            }
        )
        
        return result
