"""
Gallery access API routes.

Guests unlock a wedding gallery with an Event Code + Password instead of
creating an account. A successful unlock returns a session token scoped
to that one event.
"""

import logging

from fastapi import APIRouter, status
from sqlalchemy import select
from pydantic import BaseModel, Field

from app.database import async_session_maker
from app.models.event import Event
from app.models.photo import Photo
from app.services.auth import verify_password, create_gallery_token
from app.exceptions import ValidationError

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/gallery", tags=["gallery"])


class GalleryAccessRequest(BaseModel):
    """Request model for unlocking a gallery."""
    access_code: str = Field(..., min_length=1, max_length=12)
    password: str = Field(..., min_length=1, max_length=64)


@router.post(
    "/access",
    status_code=status.HTTP_200_OK,
    summary="Unlock a private wedding gallery",
    description="Exchange an Event Code + Password for a session token scoped to that event"
)
async def access_gallery(request: GalleryAccessRequest):
    """
    Verify an event access code + password and issue a session token.

    Args:
        request: Access code and password submitted by the guest

    Returns:
        Session token plus enough event info to render the gallery hero

    Raises:
        ValidationError: If the code/password combination is invalid
    """
    # Codes are generated uppercase; normalize input so guests aren't
    # tripped up by case.
    access_code = request.access_code.strip().upper()

    async with async_session_maker() as db:
        result = await db.execute(
            select(Event).where(Event.access_code == access_code)
        )
        event = result.scalar_one_or_none()

        # Same error for "code not found" and "wrong password" - don't
        # reveal which part was wrong.
        if not event or not verify_password(request.password, event.password_hash):
            logger.warning(f"Failed gallery access attempt for code={access_code}")
            raise ValidationError("Incorrect event code or password")

        photo_count_result = await db.execute(
            select(Photo).where(Photo.event_id == event.event_id)
            .order_by(Photo.uploaded_at.desc())
        )
        photos = photo_count_result.scalars().all()
        cover_photo = photos[0].file_path if photos else None

        token = create_gallery_token(event.event_id)

        logger.info(f"Gallery unlocked: event_id={event.event_id}, name={event.name}")

        return {
            "success": True,
            "message": "Gallery unlocked successfully",
            "data": {
                "token": token,
                "event_id": event.event_id,
                "name": event.name,
                "event_date": event.event_date.isoformat() if event.event_date else None,
                "photo_count": len(photos),
                "cover_photo": cover_photo,
            }
        }
