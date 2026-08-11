"""
Photo API routes.

This module defines API endpoints for photo upload and face search operations.
"""

import logging
from typing import Annotated, Optional

from fastapi import APIRouter, Depends, Header, UploadFile, File, Form, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from app.database import get_db
from app.api.schemas import (
    PhotoUploadResponse, PhotoUploadData,
    FaceSearchResponse, FaceSearchData, PhotoMatch, BoundingBox,
    HealthCheckResponse, HealthCheckData
)
from app.services import (
    ImageValidator,
    FileStorageService,
    get_face_service,
    PhotoService
)
from app.repositories import PhotoRepository
from app.exceptions import ValidationError
from app.services.auth import verify_gallery_access


logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/api/photos", tags=["photos"])


# Dependency to create PhotoService with all dependencies
async def get_photo_service(db: AsyncSession = Depends(get_db)) -> PhotoService:
    """
    Create PhotoService with all dependencies.
    
    Args:
        db: Database session from dependency injection
        
    Returns:
        PhotoService instance
    """
    from app.config import get_settings
    settings = get_settings()
    
    photo_repo = PhotoRepository(db)
    image_validator = ImageValidator()
    file_storage = FileStorageService()
    face_service = get_face_service()
    
    # Initialize R2 storage if configured (cached singleton - avoids
    # rebuilding the boto3 client/connection pool on every request)
    r2_storage = None
    if settings.STORAGE_TYPE == 'r2':
        from app.services.r2_storage import get_r2_storage_service
        try:
            r2_storage = get_r2_storage_service()
        except ValueError as e:
            logger.warning(f"R2 storage not configured properly: {e}")
    
    return PhotoService(
        photo_repository=photo_repo,
        image_validator=image_validator,
        file_storage=file_storage,
        face_service=face_service,
        r2_storage=r2_storage
    )


@router.post(
    "/upload",
    response_model=PhotoUploadResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload a photo to an event",
    description="""
    Upload a photo to a wedding event with automatic face detection.
    
    The system will:
    1. Validate the image (format, size, dimensions)
    2. Detect all faces in the photo
    3. Extract facial embeddings for similarity search
    4. Store the photo and embeddings in the database
    
    Supported formats: JPEG, PNG, WEBP
    Maximum file size: 10MB
    Maximum dimensions: 8000x8000 pixels
    
    If no faces are detected, the photo is still stored but won't be searchable by face.
    """
)
async def upload_photo(
    file: Annotated[UploadFile, File(description="Image file to upload")],
    event_id: Annotated[int, Form(description="ID of the event this photo belongs to")],
    skip_face_detection: Annotated[bool, Form(description="Skip face detection for faster upload")] = False,
    category: Annotated[Optional[str], Form(description="Optional sub-category label, e.g. the folder name (Haldi, Groom Home)")] = None,
    photo_service: PhotoService = Depends(get_photo_service),
    db: AsyncSession = Depends(get_db)
) -> PhotoUploadResponse:
    """
    Upload a photo to an event with face detection.
    
    Args:
        file: Uploaded image file
        event_id: ID of the event
        photo_service: Photo service (injected)
        db: Database session (injected)
        
    Returns:
        PhotoUploadResponse with photo_id, face_count, and optional warning
        
    Raises:
        ValidationError: If image validation fails (400)
        EventNotFoundError: If event doesn't exist (404)
        DatabaseError: If database operation fails (503)
    """
    logger.info(
        f"Photo upload request: filename={file.filename}, event_id={event_id}",
        extra={"uploaded_filename": file.filename, "event_id": event_id}
    )
    
    # Validate file was provided
    if not file:
        raise ValidationError("No file provided")
    
    # Validate content type (preliminary check)
    if file.content_type not in ["image/jpeg", "image/png", "image/webp"]:
        raise ValidationError(
            f"Unsupported content type: {file.content_type}. "
            "Supported types: image/jpeg, image/png, image/webp"
        )
    
    # Read file content
    file_content = await file.read()
    
    # Upload and process photo
    result = await photo_service.upload_photo(
        file_content=file_content,
        filename=file.filename or "unknown",
        event_id=event_id,
        skip_face_detection=skip_face_detection,
        category=category.strip() if category and category.strip() else None
    )
    
    # Commit transaction
    await db.commit()

    from app.services.cache import events_list_cache, event_photos_cache
    events_list_cache.invalidate("all")
    event_photos_cache.invalidate(str(event_id))

    # Prepare response message
    if skip_face_detection:
        message = "Photo uploaded successfully (face detection skipped for speed)"
    elif result.warning:
        message = f"Photo uploaded with warning: {result.warning}"
    elif result.face_count == 0:
        message = "Photo uploaded but no faces detected"
    elif result.face_count == 1:
        message = "Photo uploaded successfully with 1 face detected"
    else:
        message = f"Photo uploaded successfully with {result.face_count} faces detected"
    
    # Return response
    return PhotoUploadResponse(
        success=True,
        message=message,
        data=PhotoUploadData(
            photo_id=result.photo_id,
            file_path=result.file_path,
            face_count=result.face_count,
            faces_stored=result.faces_stored,
            warning=result.warning
        )
    )


@router.post(
    "/search",
    response_model=FaceSearchResponse,
    status_code=status.HTTP_200_OK,
    summary="Search for photos by face",
    description="""
    Upload a selfie to find all photos from an event containing your face.
    
    The system will:
    1. Detect the face in your selfie
    2. Generate a facial embedding
    3. Search all photos in the event for similar faces
    4. Return matching photos ordered by similarity
    
    If multiple faces are detected in the selfie, the largest face is used.
    
    Supported formats: JPEG, PNG, WEBP
    Maximum file size: 10MB
    """
)
async def search_by_face(
    selfie: Annotated[UploadFile, File(description="Selfie image to search for")],
    event_id: Annotated[int, Form(description="ID of the event to search in")],
    threshold: Annotated[float, Form(description="Minimum similarity threshold (0.0 to 1.0)", ge=0.0, le=1.0)] = 0.6,
    photo_service: PhotoService = Depends(get_photo_service),
    db: AsyncSession = Depends(get_db),
    authorization: Annotated[Optional[str], Header()] = None
) -> FaceSearchResponse:
    """
    Search for photos containing a face similar to the uploaded selfie.

    Args:
        selfie: Uploaded selfie image
        event_id: ID of the event to search in
        threshold: Minimum similarity threshold (default: 0.6)
        photo_service: Photo service (injected)
        db: Database session (injected)
        authorization: Bearer gallery session token, scoped to event_id

    Returns:
        FaceSearchResponse with list of matching photos

    Raises:
        UnauthorizedError: If the access token is missing or invalid (401)
        ForbiddenError: If the token isn't scoped to this event (403)
        ValidationError: If selfie validation fails or no face detected (400)
        EventNotFoundError: If event doesn't exist (404)
        DatabaseError: If database operation fails (503)
    """
    verify_gallery_access(authorization, event_id)

    logger.info(
        f"Face search request: filename={selfie.filename}, event_id={event_id}, threshold={threshold}",
        extra={
            "uploaded_filename": selfie.filename,
            "event_id": event_id,
            "threshold": threshold
        }
    )
    
    # Validate file was provided
    if not selfie:
        raise ValidationError("No selfie file provided")
    
    # Validate content type (preliminary check)
    if selfie.content_type not in ["image/jpeg", "image/png", "image/webp"]:
        raise ValidationError(
            f"Unsupported content type: {selfie.content_type}. "
            "Supported types: image/jpeg, image/png, image/webp"
        )
    
    # Read file content
    selfie_content = await selfie.read()
    
    # Search for similar faces
    search_result = await photo_service.search_faces(
        selfie_content=selfie_content,
        selfie_filename=selfie.filename or "selfie",
        event_id=event_id,
        threshold=threshold
    )
    
    # Convert matches to response format
    matches = [
        PhotoMatch(
            photo_id=match["photo_id"],
            file_path=match["file_path"],
            embedding_id=match["embedding_id"],
            bounding_box=BoundingBox(
                x1=match["bounding_box"]["x1"],
                y1=match["bounding_box"]["y1"],
                x2=match["bounding_box"]["x2"],
                y2=match["bounding_box"]["y2"]
            ),
            confidence_score=match["confidence_score"],
            similarity_score=match["similarity_score"]
        )
        for match in search_result["matches"]
    ]
    
    # Prepare response message
    num_matches = search_result["num_matches"]
    if num_matches == 0:
        message = "No matching photos found"
    elif num_matches == 1:
        message = "Found 1 matching photo"
    else:
        message = f"Found {num_matches} matching photos"
    
    # Return response
    return FaceSearchResponse(
        success=True,
        message=message,
        data=FaceSearchData(
            matches=matches,
            num_matches=num_matches,
            query_face_confidence=search_result["query_face_confidence"],
            threshold_used=search_result["threshold_used"]
        )
    )


@router.get(
    "/event/{event_id}",
    status_code=status.HTTP_200_OK,
    summary="Get all photos from an event",
    description="Retrieve all photos belonging to a specific event for gallery display"
)
async def get_event_photos(
    event_id: int,
    db: AsyncSession = Depends(get_db),
    authorization: Annotated[Optional[str], Header()] = None
):
    """
    Get all photos from an event.

    Args:
        event_id: ID of the event
        db: Database session
        authorization: Bearer gallery session token, scoped to event_id

    Returns:
        List of photos with metadata

    Raises:
        UnauthorizedError: If the access token is missing or invalid (401)
        ForbiddenError: If the token isn't scoped to this event (403)
    """
    verify_gallery_access(authorization, event_id)

    from app.repositories import PhotoRepository
    from app.services.cache import event_photos_cache

    cache_key = str(event_id)
    cached = event_photos_cache.get(cache_key)
    if cached is not None:
        return cached

    photo_repo = PhotoRepository(db)

    # Verify event exists
    await photo_repo.verify_event_exists(event_id)

    # Get all photos for this event
    from sqlalchemy import select
    from app.models.photo import Photo

    result = await db.execute(
        select(Photo).where(Photo.event_id == event_id).order_by(Photo.uploaded_at.desc())
    )
    photos = result.scalars().all()

    response = {
        "success": True,
        "message": f"Retrieved {len(photos)} photos",
        "data": {
            "event_id": event_id,
            "photos": [
                {
                    "photo_id": photo.photo_id,
                    "file_path": photo.file_path,
                    "photo_metadata": photo.photo_metadata,
                    "uploaded_at": photo.uploaded_at.isoformat()
                }
                for photo in photos
            ]
        }
    }
    event_photos_cache.set(cache_key, response)
    return response
