"""
In-memory job status tracking for background face processing tasks.

Replaces Celery's AsyncResult now that face processing runs as a FastAPI
BackgroundTask in the same process, instead of a separate Celery worker.
Status is lost on server restart, but processing is idempotent (it only
ever picks up photos without embeddings), so a re-triggered job just
picks up where the last one left off.
"""

import threading
from typing import Any, Dict, Optional


class JobStore:
    def __init__(self):
        self._jobs: Dict[str, Dict[str, Any]] = {}
        self._lock = threading.Lock()

    def create(self, job_id: str) -> None:
        with self._lock:
            self._jobs[job_id] = {
                "status": "pending",
                "progress": None,
                "result": None,
                "error": None,
                "cancel_requested": False,
            }

    def update(self, job_id: str, **fields: Any) -> None:
        with self._lock:
            if job_id in self._jobs:
                self._jobs[job_id].update(fields)

    def get(self, job_id: str) -> Optional[Dict[str, Any]]:
        with self._lock:
            job = self._jobs.get(job_id)
            return dict(job) if job else None

    def request_cancel(self, job_id: str) -> bool:
        with self._lock:
            if job_id not in self._jobs:
                return False
            self._jobs[job_id]["cancel_requested"] = True
            return True

    def is_cancel_requested(self, job_id: str) -> bool:
        with self._lock:
            job = self._jobs.get(job_id)
            return bool(job and job.get("cancel_requested"))


job_store = JobStore()
