"""
Guest registration and match review API endpoints.
Provides QR registration, AWS Rekognition matching, studio review queue, and guest gallery delivery.
"""

import logging
import os
from datetime import datetime
from typing import Annotated, List, Optional
from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile, status
from pydantic import BaseModel
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.event import Event
from app.models.photo import Photo
from app.models.guest import Guest
from app.models.guest_match import GuestMatch
from app.services.aws_rekognition import get_aws_rekognition_service
from app.services.file_storage import FileStorageService
from app.config import get_settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["guests_and_matches"])


class MatchActionRequest(BaseModel):
    action: str  # "approve" or "reject"


@router.post("/guests/register", status_code=status.HTTP_201_CREATED)
async def register_guest(
    name: Annotated[str, Form(description="Guest full name")],
    phone: Annotated[str, Form(description="Guest WhatsApp phone number")],
    event_id: Annotated[int, Form(description="Event ID")],
    selfie: Annotated[UploadFile, File(description="Selfie image")],
    consent: Annotated[bool, Form(description="Consent agreement")] = True,
    db: AsyncSession = Depends(get_db),
):
    """
    Guest scans event QR code and registers with a clear selfie.
    Triggers AWS Rekognition face comparison against event photos.
    """
    if not consent:
        raise HTTPException(status_code=400, detail="Consent is required to register for photos.")

    # Verify event exists
    event_res = await db.execute(select(Event).where(Event.event_id == event_id))
    event = event_res.scalar_one_or_none()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found.")

    # Read selfie bytes
    selfie_bytes = await selfie.read()
    if len(selfie_bytes) == 0:
        raise HTTPException(status_code=400, detail="Empty selfie file uploaded.")

    # Save selfie to storage
    file_storage = FileStorageService()
    selfie_ext = os.path.splitext(selfie.filename or ".jpg")[1] or ".jpg"
    selfie_path = file_storage.save_file(
        file_content=selfie_bytes,
        extension=selfie_ext,
        subdirectory=f"selfies/event_{event_id}",
    )

    # Create Guest record
    guest = Guest(
        event_id=event_id,
        name=name.strip(),
        phone=phone.strip(),
        selfie_path=selfie_path,
        status="registered",
    )
    db.add(guest)
    await db.flush()  # to obtain guest_id

    # Find existing photos in this event to run face matching
    photos_res = await db.execute(
        select(Photo).where(Photo.event_id == event_id).order_by(Photo.photo_id.desc())
    )
    photos = photos_res.scalars().all()

    rekognition = get_aws_rekognition_service()
    has_pending = False
    confirmed_count = 0

    # Compare selfie against existing event photos
    for photo in photos:
        try:
            full_photo_path = file_storage.get_absolute_path(photo.file_path)
            if not os.path.exists(full_photo_path):
                continue
            with open(full_photo_path, "rb") as f:
                photo_bytes = f.read()

            matches = rekognition.compare_faces(
                source_image_bytes=selfie_bytes,
                target_image_bytes=photo_bytes,
            )

            for m in matches:
                guest_match = GuestMatch(
                    event_id=event_id,
                    guest_id=guest.guest_id,
                    photo_id=photo.photo_id,
                    similarity=m.similarity,
                    confidence=m.confidence,
                    status=m.tier,  # "confirmed" or "pending_review"
                    bounding_box=m.bounding_box,
                )
                db.add(guest_match)

                if m.is_review_required:
                    has_pending = True
                elif m.tier == "confirmed":
                    confirmed_count += 1
        except Exception as e:
            logger.warning(f"Error matching photo {photo.photo_id}: {e}")

    # Update guest status
    if has_pending:
        guest.status = "needs_review"
    elif confirmed_count > 0:
        guest.status = "matched"
    else:
        guest.status = "registered"

    await db.commit()
    await db.refresh(guest)

    return {
        "success": True,
        "message": "Registration successful. Photos matched.",
        "data": {
            "guest_id": guest.guest_id,
            "name": guest.name,
            "phone": guest.phone,
            "status": guest.status,
            "selfie_path": guest.selfie_path,
            "confirmed_matches": confirmed_count,
            "needs_review": has_pending,
        },
    }


@router.get("/guests", status_code=status.HTTP_200_OK)
async def list_guests(
    event_id: Optional[int] = Query(None, description="Filter by event ID"),
    db: AsyncSession = Depends(get_db),
):
    """List all registered guests, their match counts, and status."""
    query = select(Guest)
    if event_id:
        query = query.where(Guest.event_id == event_id)
    query = query.order_by(Guest.guest_id.desc())

    res = await db.execute(query)
    guests = res.scalars().all()

    data = []
    for g in guests:
        # Count confirmed matches
        matches_res = await db.execute(
            select(func.count(GuestMatch.match_id)).where(
                and_(GuestMatch.guest_id == g.guest_id, GuestMatch.status == "confirmed")
            )
        )
        conf_count = matches_res.scalar_one() or 0

        # Count pending reviews
        pending_res = await db.execute(
            select(func.count(GuestMatch.match_id)).where(
                and_(GuestMatch.guest_id == g.guest_id, GuestMatch.status == "pending_review")
            )
        )
        pend_count = pending_res.scalar_one() or 0

        data.append({
            "guest_id": g.guest_id,
            "event_id": g.event_id,
            "name": g.name,
            "phone": g.phone,
            "status": g.status,
            "selfie_path": g.selfie_path,
            "created_at": g.created_at.isoformat(),
            "photos_count": conf_count,
            "pending_review_count": pend_count,
        })

    return {
        "success": True,
        "data": data,
        "total": len(data),
    }


@router.get("/matches/review", status_code=status.HTTP_200_OK)
async def get_matches_for_review(
    event_id: Optional[int] = Query(None, description="Event ID to filter review queue"),
    db: AsyncSession = Depends(get_db),
):
    """
    Get all pending uncertain matches (60% - 84.9% similarity)
    needing manual approval from the studio owner.
    """
    query = select(GuestMatch, Guest, Photo).join(
        Guest, GuestMatch.guest_id == Guest.guest_id
    ).join(
        Photo, GuestMatch.photo_id == Photo.photo_id
    ).where(GuestMatch.status == "pending_review")

    if event_id:
        query = query.where(GuestMatch.event_id == event_id)

    query = query.order_by(GuestMatch.similarity.desc())
    res = await db.execute(query)
    rows = res.all()

    # Group by guest
    guest_groups = {}
    for match, guest, photo in rows:
        if guest.guest_id not in guest_groups:
            guest_groups[guest.guest_id] = {
                "guest_id": guest.guest_id,
                "name": guest.name,
                "phone": guest.phone,
                "selfie_path": guest.selfie_path,
                "candidates": [],
            }
        guest_groups[guest.guest_id]["candidates"].append({
            "match_id": match.match_id,
            "photo_id": photo.photo_id,
            "file_path": photo.file_path,
            "similarity": match.similarity,
            "confidence": match.confidence,
            "bounding_box": match.bounding_box,
            "photo_metadata": photo.photo_metadata,
        })

    return {
        "success": True,
        "data": list(guest_groups.values()),
        "total_guests": len(guest_groups),
        "total_pending_matches": len(rows),
    }


@router.post("/matches/{match_id}/action", status_code=status.HTTP_200_OK)
async def action_match(
    match_id: int,
    req: MatchActionRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Approve or reject an uncertain face match.
    - 'approve': adds to confirmed guest gallery
    - 'reject': excludes photo from guest gallery
    """
    res = await db.execute(select(GuestMatch).where(GuestMatch.match_id == match_id))
    match = res.scalar_one_or_none()
    if not match:
        raise HTTPException(status_code=404, detail="Match record not found.")

    if req.action == "approve":
        match.status = "confirmed"
    elif req.action == "reject":
        match.status = "rejected"
    else:
        raise HTTPException(status_code=400, detail="Invalid action. Use 'approve' or 'reject'.")

    match.reviewed_at = datetime.utcnow()

    # Check if guest has any remaining pending reviews
    pending_left = await db.execute(
        select(func.count(GuestMatch.match_id)).where(
            and_(
                GuestMatch.guest_id == match.guest_id,
                GuestMatch.match_id != match_id,
                GuestMatch.status == "pending_review",
            )
        )
    )
    if (pending_left.scalar_one() or 0) == 0:
        # No more pending matches, update guest status
        guest_res = await db.execute(select(Guest).where(Guest.guest_id == match.guest_id))
        guest = guest_res.scalar_one_or_none()
        if guest and guest.status == "needs_review":
            guest.status = "matched"

    await db.commit()

    return {
        "success": True,
        "message": f"Match marked as {match.status}.",
        "match_id": match_id,
        "new_status": match.status,
    }


@router.get("/gallery/guest/{guest_id}", status_code=status.HTTP_200_OK)
async def get_guest_gallery(
    guest_id: int,
    db: AsyncSession = Depends(get_db),
):
    """
    Retrieve confirmed photos for a guest's private gallery.
    Photos are categorized into Haldi, Mehendi, Sangeet, Shaadi, Reception, Other.
    """
    guest_res = await db.execute(select(Guest).where(Guest.guest_id == guest_id))
    guest = guest_res.scalar_one_or_none()
    if not guest:
        raise HTTPException(status_code=404, detail="Guest not found.")

    event_res = await db.execute(select(Event).where(Event.event_id == guest.event_id))
    event = event_res.scalar_one_or_none()

    # Get confirmed matches with photo metadata
    matches_res = await db.execute(
        select(GuestMatch, Photo)
        .join(Photo, GuestMatch.photo_id == Photo.photo_id)
        .where(and_(GuestMatch.guest_id == guest_id, GuestMatch.status == "confirmed"))
        .order_by(GuestMatch.similarity.desc())
    )
    rows = matches_res.all()

    photos_by_category = {
        "Haldi": [],
        "Mehendi": [],
        "Sangeet": [],
        "Shaadi": [],
        "Reception": [],
        "Other": [],
    }

    all_photos = []
    for match, photo in rows:
        cat = "Other"
        if photo.photo_metadata and isinstance(photo.photo_metadata, dict):
            cat = photo.photo_metadata.get("category") or "Other"
        if cat not in photos_by_category:
            photos_by_category[cat] = []

        item = {
            "photo_id": photo.photo_id,
            "file_path": photo.file_path,
            "category": cat,
            "similarity": match.similarity,
            "uploaded_at": photo.uploaded_at.isoformat() if photo.uploaded_at else None,
        }
        photos_by_category[cat].append(item)
        all_photos.append(item)

    return {
        "success": True,
        "data": {
            "guest": {
                "guest_id": guest.guest_id,
                "name": guest.name,
                "phone": guest.phone,
                "status": guest.status,
            },
            "event": {
                "event_id": event.event_id if event else None,
                "name": event.name if event else "Celebration",
                "event_date": event.event_date.isoformat() if event and event.event_date else None,
            },
            "total_photos": len(all_photos),
            "photos": all_photos,
            "by_category": photos_by_category,
        },
    }
