"""
Event management API routes.

This module provides endpoints for creating and managing wedding events.
"""

import logging
from datetime import date
from typing import Optional

from fastapi import APIRouter, BackgroundTasks, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from pydantic import BaseModel, Field

from app.database import get_db
from app.models.event import Event
from app.models.face_embedding import FaceEmbedding
from app.exceptions import EventNotFoundError

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/events", tags=["events"])


# Request/Response Models
class EventCreate(BaseModel):
    """Request model for creating a new event."""
    name: str = Field(..., min_length=1, max_length=200, description="Event name")
    # Required - the events table has a NOT NULL constraint on event_date.
    event_date: date = Field(..., description="Event date")


class EventResponse(BaseModel):
    """Response model for event data."""
    event_id: int
    name: str
    event_date: Optional[date]
    created_at: str
    photo_count: int = 0


class EventListResponse(BaseModel):
    """Response model for list of events."""
    success: bool
    message: str
    data: dict


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    summary="Create a new event",
    description="Create a new wedding event for photo organization"
)
async def create_event(
    event_data: EventCreate,
    db: AsyncSession = Depends(get_db)
):
    """
    Create a new private event with a generated access code + password.

    The plaintext password is only ever returned in this response - it's
    stored as a bcrypt hash from here on, so the photographer must save
    or share it now.

    Args:
        event_data: Event creation data
        db: Database session

    Returns:
        Created event details, including the one-time plaintext credentials
    """
    from app.services.auth import generate_access_code, generate_password, hash_password

    logger.info(f"Creating new event: {event_data.name}")

    # Generate a unique access code (astronomically unlikely to collide,
    # but retry on the rare chance it does)
    access_code = generate_access_code()
    while (await db.execute(
        select(Event).where(Event.access_code == access_code)
    )).scalar_one_or_none():
        access_code = generate_access_code()

    password = generate_password()

    event = Event(
        name=event_data.name,
        event_date=event_data.event_date,
        access_code=access_code,
        password_hash=hash_password(password)
    )

    db.add(event)
    await db.commit()
    await db.refresh(event)

    from app.services.cache import events_list_cache
    events_list_cache.invalidate("all")

    logger.info(f"Event created: ID={event.event_id}, name={event.name}, access_code={access_code}")

    return {
        "success": True,
        "message": "Event created successfully",
        "data": {
            "event_id": event.event_id,
            "name": event.name,
            "event_date": event.event_date.isoformat() if event.event_date else None,
            "created_at": event.created_at.isoformat(),
            "access_code": access_code,
            "password": password
        }
    }


@router.get(
    "",
    status_code=status.HTTP_200_OK,
    summary="List all events",
    description="Get all events with photo counts"
)
async def list_events(
    db: AsyncSession = Depends(get_db)
):
    """
    List all events with photo counts.

    Args:
        db: Database session

    Returns:
        List of events with metadata
    """
    from app.models.photo import Photo
    from app.services.cache import events_list_cache

    cached = events_list_cache.get("all")
    if cached is not None:
        return cached

    # Get all events with photo counts
    result = await db.execute(
        select(
            Event.event_id,
            Event.name,
            Event.event_date,
            Event.created_at,
            Event.access_code,
            func.count(Photo.photo_id).label('photo_count')
        )
        .outerjoin(Photo, Event.event_id == Photo.event_id)
        .group_by(Event.event_id)
        .order_by(Event.created_at.desc())
    )

    events_data = result.all()

    events = [
        {
            "event_id": row.event_id,
            "name": row.name,
            "event_date": row.event_date.isoformat() if row.event_date else None,
            "created_at": row.created_at.isoformat(),
            "access_code": row.access_code,
            "photo_count": row.photo_count
        }
        for row in events_data
    ]
    
    logger.info(f"Retrieved {len(events)} events")

    response = {
        "success": True,
        "message": f"Retrieved {len(events)} events",
        "data": {
            "events": events,
            "total": len(events)
        }
    }
    events_list_cache.set("all", response)
    return response


@router.get(
    "/{event_id}",
    status_code=status.HTTP_200_OK,
    summary="Get event details",
    description="Get details of a specific event"
)
async def get_event(
    event_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    Get event details.
    
    Args:
        event_id: Event ID
        db: Database session
        
    Returns:
        Event details with photo count
    """
    from app.models.photo import Photo
    
    # Get event with photo count
    result = await db.execute(
        select(
            Event.event_id,
            Event.name,
            Event.event_date,
            Event.created_at,
            Event.updated_at,
            func.count(Photo.photo_id).label('photo_count')
        )
        .outerjoin(Photo, Event.event_id == Photo.event_id)
        .where(Event.event_id == event_id)
        .group_by(Event.event_id)
    )
    
    event_data = result.first()
    
    if not event_data:
        raise EventNotFoundError(event_id)
    
    return {
        "success": True,
        "message": "Event retrieved successfully",
        "data": {
            "event_id": event_data.event_id,
            "name": event_data.name,
            "event_date": event_data.event_date.isoformat() if event_data.event_date else None,
            "created_at": event_data.created_at.isoformat(),
            "updated_at": event_data.updated_at.isoformat(),
            "photo_count": event_data.photo_count
        }
    }


@router.delete(
    "/{event_id}",
    status_code=status.HTTP_200_OK,
    summary="Delete an event",
    description="Delete an event and all its photos"
)
async def delete_event(
    event_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    Delete an event and all associated photos, including their stored
    image files (R2 or local storage). Face embeddings are removed via
    DB cascade along with the photos.

    Args:
        event_id: Event ID to delete
        db: Database session

    Returns:
        Success message
    """
    from urllib.parse import urlparse
    from app.models.photo import Photo
    from app.config import get_settings

    # Check if event exists
    result = await db.execute(
        select(Event).where(Event.event_id == event_id)
    )
    event = result.scalar_one_or_none()

    if not event:
        raise EventNotFoundError(event_id)

    # Collect photo file paths before deleting DB rows
    photos_result = await db.execute(
        select(Photo.file_path).where(Photo.event_id == event_id)
    )
    file_paths = [row[0] for row in photos_result.all()]

    # Delete the underlying image files (R2 or local storage)
    settings = get_settings()
    deleted_files = 0
    if file_paths:
        if settings.STORAGE_TYPE == 'r2':
            from app.services.r2_storage import get_r2_storage_service
            r2_storage = get_r2_storage_service()
            for file_path in file_paths:
                try:
                    key = urlparse(file_path).path.lstrip('/')
                    if r2_storage.delete_file(key):
                        deleted_files += 1
                except Exception as e:
                    logger.warning(f"Failed to delete R2 object for {file_path}: {str(e)}")
        else:
            from app.services.file_storage import FileStorageService
            file_storage = FileStorageService()
            for file_path in file_paths:
                try:
                    if file_storage.delete_file(file_path):
                        deleted_files += 1
                except Exception as e:
                    logger.warning(f"Failed to delete local file {file_path}: {str(e)}")

    # Delete event (cascade will delete photos and embeddings)
    await db.delete(event)
    await db.commit()

    from app.services.cache import events_list_cache, event_photos_cache
    events_list_cache.invalidate("all")
    event_photos_cache.invalidate(str(event_id))

    logger.info(
        f"Event deleted: ID={event_id}, name={event.name}, "
        f"{deleted_files}/{len(file_paths)} stored files removed"
    )

    return {
        "success": True,
        "message": f"Event '{event.name}' and {deleted_files} photo(s) deleted successfully",
        "data": {
            "event_id": event_id,
            "photos_deleted": len(file_paths),
            "files_deleted": deleted_files
        }
    }


@router.post(
    "/{event_id}/process-faces",
    status_code=status.HTTP_202_ACCEPTED,
    summary="Process faces for all photos in event (background)",
    description="Queue a background job to run face detection on all photos in an event that don't have embeddings yet"
)
async def process_event_faces(
    event_id: int,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    """
    Process faces for all photos in an event (background job).

    This endpoint queues an in-process FastAPI background task to run face
    detection on all photos that were uploaded with skip_face_detection=true
    and don't have embeddings yet.

    The job runs asynchronously in the background. Use the returned job_id to
    check status at GET /api/jobs/{job_id}/status

    Args:
        event_id: Event ID to process
        background_tasks: FastAPI background task runner
        db: Database session

    Returns:
        Job ID for status tracking
    """
    from uuid import uuid4
    from app.repositories import PhotoRepository
    from app.services.job_store import job_store
    from app.tasks.face_processing import process_faces_background

    logger.info(f"Queuing background face processing for event {event_id}")

    # Verify event exists
    photo_repo = PhotoRepository(db)
    await photo_repo.verify_event_exists(event_id)

    # Queue the background task
    job_id = str(uuid4())
    job_store.create(job_id)
    background_tasks.add_task(process_faces_background, job_id, event_id)

    logger.info(f"Face processing task queued: job_id={job_id}, event_id={event_id}")

    return {
        "success": True,
        "message": "Face processing job queued successfully",
        "data": {
            "job_id": job_id,
            "event_id": event_id,
            "status": "queued",
            "status_url": f"/api/jobs/{job_id}/status"
        }
    }
