"""
Job status tracking API routes.

Tracks background face-processing jobs that run as in-process FastAPI
BackgroundTasks (see app.services.job_store), rather than a separate
Celery worker.
"""

import logging
from typing import Optional
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

from app.services.job_store import job_store

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/jobs", tags=["jobs"])


class JobStatusResponse(BaseModel):
    """Response model for job status."""
    job_id: str
    status: str
    result: Optional[dict] = None
    error: Optional[str] = None
    progress: Optional[dict] = None


@router.get(
    "/{job_id}/status",
    status_code=status.HTTP_200_OK,
    response_model=JobStatusResponse,
    summary="Get job status",
    description="Get the current status and progress of a background job"
)
async def get_job_status(job_id: str):
    """
    Get the status of a background job.

    Args:
        job_id: The background job ID

    Returns:
        Job status information including progress
    """
    logger.info(f"Checking status for job {job_id}")

    job = job_store.get(job_id)

    if job is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job {job_id} not found"
        )

    logger.info(f"Job {job_id} status: {job['status']}")

    return {
        "job_id": job_id,
        "status": job["status"],
        "result": job.get("result"),
        "error": job.get("error"),
        "progress": job.get("progress"),
    }


@router.delete(
    "/{job_id}",
    status_code=status.HTTP_200_OK,
    summary="Cancel job",
    description="Request cancellation of a running background job"
)
async def cancel_job(job_id: str):
    """
    Request cancellation of a background job.

    Cancellation is cooperative: the job checks for the cancel request
    between photos and stops there, rather than being forcibly killed.

    Args:
        job_id: The background job ID

    Returns:
        Success message
    """
    logger.info(f"Canceling job {job_id}")

    job = job_store.get(job_id)

    if job is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job {job_id} not found"
        )

    if job["status"] in ("success", "failure", "canceled"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot cancel job in state: {job['status']}"
        )

    job_store.request_cancel(job_id)

    logger.info(f"Cancellation requested for job {job_id}")

    return {
        "success": True,
        "message": f"Cancellation requested for job {job_id}",
        "data": {
            "job_id": job_id
        }
    }
