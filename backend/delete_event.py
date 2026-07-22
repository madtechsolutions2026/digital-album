"""Delete an event from the database."""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from sqlalchemy import select, delete
from app.database import async_session_maker
from app.models.event import Event


async def delete_event(event_id: int):
    """Delete event by ID."""
    async with async_session_maker() as db:
        # Check if event exists
        result = await db.execute(
            select(Event).where(Event.event_id == event_id)
        )
        event = result.scalar_one_or_none()
        
        if not event:
            print(f"Event {event_id} not found.")
            return False
        
        print(f"Deleting event: {event.name} (ID: {event_id})")
        
        # Delete event (cascade will delete photos and embeddings)
        await db.delete(event)
        await db.commit()
        
        print(f"✓ Event deleted successfully!")
        return True


if __name__ == "__main__":
    event_id = int(sys.argv[1]) if len(sys.argv) > 1 else 1
    asyncio.run(delete_event(event_id))
