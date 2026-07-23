"""
Simple in-process TTL cache for read-heavy, rarely-changing endpoints
(event listing, gallery photo listing).

This is per-process only - fine for this app's current single-process
deployment. If the app ever moves to multiple worker processes, this
would need to move to a shared store (e.g. Redis) since each process
would otherwise cache independently and could serve stale data for up
to the TTL after another process's write.
"""

import time
from threading import Lock
from typing import Any, Dict, Optional, Tuple


class TTLCache:
    """Minimal thread-safe cache with per-entry expiry."""

    def __init__(self, ttl_seconds: float):
        self._ttl = ttl_seconds
        self._store: Dict[str, Tuple[float, Any]] = {}
        self._lock = Lock()

    def get(self, key: str) -> Optional[Any]:
        with self._lock:
            entry = self._store.get(key)
            if entry is None:
                return None

            expires_at, value = entry
            if time.monotonic() >= expires_at:
                del self._store[key]
                return None

            return value

    def set(self, key: str, value: Any) -> None:
        with self._lock:
            self._store[key] = (time.monotonic() + self._ttl, value)

    def invalidate(self, key: str) -> None:
        with self._lock:
            self._store.pop(key, None)

    def clear(self) -> None:
        with self._lock:
            self._store.clear()


# GET /api/events - single logical key. Invalidated on event create/delete
# and on photo upload (photo_count changes).
events_list_cache = TTLCache(ttl_seconds=15)

# GET /api/photos/event/{id} - keyed by event_id. Invalidated on photo
# upload and event delete.
event_photos_cache = TTLCache(ttl_seconds=15)
