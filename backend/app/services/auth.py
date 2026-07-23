"""
Event access credentials and gallery session tokens.

Weddings are private events accessed by an Event Code + Password (no guest
accounts). This module generates those credentials, hashes/verifies the
password, and issues/verifies signed session tokens scoped to one event.
"""

import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional

import bcrypt
import jwt

from app.config import get_settings
from app.exceptions import UnauthorizedError, ForbiddenError

# Excludes visually ambiguous characters (0/O, 1/I/L) since these are
# read off a screen and typed by hand.
_CODE_ALPHABET = "ABCDEFGHJKMNPQRSTUVWXYZ23456789"

JWT_ALGORITHM = "HS256"
TOKEN_TTL_DAYS = 30


def generate_access_code(length: int = 6) -> str:
    """Generate a random, human-typeable event access code."""
    return ''.join(secrets.choice(_CODE_ALPHABET) for _ in range(length))


def generate_password(length: int = 8) -> str:
    """Generate a random, human-typeable event password."""
    return ''.join(secrets.choice(_CODE_ALPHABET) for _ in range(length))


def hash_password(password: str) -> str:
    """Hash a plaintext password for storage."""
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')


def verify_password(password: str, password_hash: str) -> bool:
    """Check a plaintext password against a stored bcrypt hash."""
    try:
        return bcrypt.checkpw(password.encode('utf-8'), password_hash.encode('utf-8'))
    except ValueError:
        # Malformed hash - treat as no match rather than raising
        return False


def create_gallery_token(event_id: int) -> str:
    """Issue a signed session token scoped to a single event."""
    settings = get_settings()
    payload = {
        "event_id": event_id,
        "exp": datetime.now(timezone.utc) + timedelta(days=TOKEN_TTL_DAYS),
    }
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=JWT_ALGORITHM)


def decode_gallery_token(token: str) -> Optional[int]:
    """
    Verify a gallery session token and return its event_id, or None if the
    token is missing, expired, or invalid.
    """
    settings = get_settings()
    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload.get("event_id")
    except jwt.PyJWTError:
        return None


def verify_gallery_access(authorization: Optional[str], event_id: int) -> None:
    """
    Raise HTTPException unless the given Authorization header carries a
    valid session token scoped to event_id. Call explicitly at the top of
    any gallery route that returns data for a specific event - not wired
    as a FastAPI Depends() because event_id may come from a path param or
    a form field depending on the route, and Depends() can't see which.
    """
    if not authorization or not authorization.startswith("Bearer "):
        raise UnauthorizedError("Missing access token. Please unlock this gallery first.")

    token = authorization[len("Bearer "):]
    token_event_id = decode_gallery_token(token)

    if token_event_id is None:
        raise UnauthorizedError("Your session has expired. Please unlock this gallery again.")

    if token_event_id != event_id:
        raise ForbiddenError("This access token is not valid for this event.")
