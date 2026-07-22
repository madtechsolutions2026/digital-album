"""
Check which events have photos and embeddings.
"""
import asyncio
from sqlalchemy import select, func
from app.database import async_session_maker
from app.models import Event, Photo, FaceEmbedding

async def check_events():
    async with async_session_maker() as db:
        # Get all events with photo and embedding counts
        result = await db.execute(
            select(
                Event.event_id,
                Event.name,
                func.count(Photo.photo_id.distinct()).label('photo_count'),
                func.count(FaceEmbedding.embedding_id).label('embedding_count')
            )
            .outerjoin(Photo, Event.event_id == Photo.event_id)
            .outerjoin(FaceEmbedding, Photo.photo_id == FaceEmbedding.photo_id)
            .group_by(Event.event_id)
            .order_by(Event.event_id)
        )
        
        events = result.all()
        
        print("=" * 70)
        print("EVENTS WITH PHOTOS AND EMBEDDINGS")
        print("=" * 70)
        print(f"\n{'Event ID':<12} {'Event Name':<25} {'Photos':<10} {'Embeddings'}")
        print("-" * 70)
        
        for event_id, name, photo_count, embedding_count in events:
            print(f"{event_id:<12} {name:<25} {photo_count:<10} {embedding_count}")
        
        print("\n" + "=" * 70)

asyncio.run(check_events())
