"""
Background face processing for photos.

Runs as a FastAPI BackgroundTask in the same process as the API server,
rather than a separate Celery worker. This app runs as a single instance
for one photographer at a time, so a dedicated worker process/broker was
unnecessary complexity; job progress is tracked in-memory via job_store.
"""

import logging
from typing import Dict, Any
from PIL import Image
import io
import httpx

from app.database import async_session_maker
from app.models.photo import Photo
from app.models.face_embedding import FaceEmbedding
from app.repositories import PhotoRepository
from app.services import get_face_service
from app.services.file_storage import FileStorageService
from app.services.job_store import job_store
from sqlalchemy import select, func

logger = logging.getLogger(__name__)


async def process_faces_background(job_id: str, event_id: int) -> None:
    """
    Background task to process faces for all photos in an event.

    Detects faces in photos that were uploaded without face detection,
    reporting progress via job_store for polling clients.

    Args:
        job_id: Job ID used to report status via job_store
        event_id: Event ID to process
    """
    logger.info(f"Starting background face processing for event {event_id}")
    job_store.update(job_id, status="started")

    try:
        async with async_session_maker() as db:
            photo_repo = PhotoRepository(db)
            await photo_repo.verify_event_exists(event_id)

            result = await db.execute(
                select(Photo)
                .where(Photo.event_id == event_id)
                .outerjoin(Photo.face_embeddings)
                .group_by(Photo.photo_id)
                .having(func.count(FaceEmbedding.embedding_id) == 0)
                .order_by(Photo.uploaded_at)
            )
            photos_to_process = result.scalars().all()

            if not photos_to_process:
                logger.info(f"No photos to process for event {event_id}")
                job_store.update(
                    job_id,
                    status="success",
                    result={
                        "success": True,
                        "event_id": event_id,
                        "photos_processed": 0,
                        "photos_skipped": 0,
                        "total_faces_found": 0,
                        "message": "No photos need face processing",
                    },
                )
                return

            total_photos = len(photos_to_process)
            logger.info(f"Found {total_photos} photos to process for event {event_id}")

            face_service = get_face_service()

            processed_count = 0
            skipped_count = 0
            total_faces = 0

            for idx, photo in enumerate(photos_to_process):
                if job_store.is_cancel_requested(job_id):
                    logger.info(f"Face processing for event {event_id} canceled")
                    await db.commit()
                    job_store.update(
                        job_id,
                        status="canceled",
                        progress={
                            "current": idx,
                            "total": total_photos,
                            "percent_complete": int(idx / total_photos * 100),
                            "status": "Canceled",
                        },
                    )
                    return

                job_store.update(
                    job_id,
                    status="processing",
                    progress={
                        "current": idx + 1,
                        "total": total_photos,
                        "percent_complete": int((idx + 1) / total_photos * 100),
                        "status": f"Processing photo {idx + 1} of {total_photos}",
                        "photos_processed": processed_count,
                        "faces_found": total_faces,
                    },
                )

                try:
                    # Download image from R2 or local storage
                    if photo.file_path.startswith('http'):
                        async with httpx.AsyncClient(timeout=30.0) as client:
                            response = await client.get(photo.file_path)
                            response.raise_for_status()
                            image_bytes = response.content
                    else:
                        file_storage = FileStorageService()
                        full_path = file_storage.get_full_path(photo.file_path)
                        with open(full_path, 'rb') as f:
                            image_bytes = f.read()

                    image = Image.open(io.BytesIO(image_bytes))

                    faces = await face_service.detect_faces(image)

                    if faces:
                        for face_info in faces:
                            embedding_record = FaceEmbedding(
                                photo_id=photo.photo_id,
                                embedding_vector=face_info.embedding.tolist(),
                                bounding_box={
                                    "x1": int(face_info.bbox[0]),
                                    "y1": int(face_info.bbox[1]),
                                    "x2": int(face_info.bbox[2]),
                                    "y2": int(face_info.bbox[3])
                                },
                                confidence_score=float(face_info.confidence)
                            )
                            db.add(embedding_record)

                        total_faces += len(faces)
                        processed_count += 1

                        logger.info(f"Processed photo {photo.photo_id}: found {len(faces)} faces")
                    else:
                        skipped_count += 1
                        logger.info(f"No faces in photo {photo.photo_id}")

                except Exception as e:
                    logger.error(f"Error processing photo {photo.photo_id}: {str(e)}", exc_info=True)
                    skipped_count += 1

            await db.commit()

            result = {
                "success": True,
                "event_id": event_id,
                "photos_processed": processed_count,
                "photos_skipped": skipped_count,
                "total_faces_found": total_faces,
                "total_photos_checked": total_photos,
                "message": f"Processed {processed_count} photos, found {total_faces} faces"
            }

            logger.info(
                f"Background processing complete for event {event_id}: "
                f"{processed_count} photos processed, {total_faces} faces found, {skipped_count} skipped"
            )

            job_store.update(
                job_id,
                status="success",
                result=result,
                progress={
                    "current": total_photos,
                    "total": total_photos,
                    "percent_complete": 100,
                    "status": "Complete",
                    "photos_processed": processed_count,
                    "faces_found": total_faces,
                },
            )

    except Exception as e:
        logger.error(f"Face processing failed for event {event_id}: {str(e)}", exc_info=True)
        job_store.update(job_id, status="failure", error=str(e))
