"""
Diagnose why search isn't finding matches in event 11.
"""
import asyncio
from sqlalchemy import select, func
from app.database import async_session_maker
from app.models import Event, Photo, FaceEmbedding

async def diagnose():
    async with async_session_maker() as db:
        # Check event 11 specifically
        print("=" * 70)
        print("DIAGNOSING EVENT 11")
        print("=" * 70)
        
        # Get event details
        result = await db.execute(
            select(Event).where(Event.event_id == 11)
        )
        event = result.scalar_one_or_none()
        
        if not event:
            print("\n❌ Event 11 does NOT exist!")
            print("\nLet me show you all events:\n")
            
            result = await db.execute(select(Event))
            all_events = result.scalars().all()
            
            for evt in all_events:
                print(f"Event {evt.event_id}: {evt.name}")
            
            return
        
        print(f"\n✅ Event 11 exists: {event.name}")
        
        # Count photos
        result = await db.execute(
            select(func.count(Photo.photo_id))
            .where(Photo.event_id == 11)
        )
        photo_count = result.scalar()
        print(f"   Photos: {photo_count}")
        
        # Count embeddings
        result = await db.execute(
            select(func.count(FaceEmbedding.embedding_id))
            .join(Photo)
            .where(Photo.event_id == 11)
        )
        embedding_count = result.scalar()
        print(f"   Face Embeddings: {embedding_count}")
        
        if photo_count == 0:
            print("\n❌ Event 11 has NO photos! You need to upload photos to this event first.")
        elif embedding_count == 0:
            print("\n❌ Event 11 has photos but NO face embeddings!")
            print("   This means either:")
            print("   1. Face processing hasn't run yet (click 'Done & Process Faces' after upload)")
            print("   2. No faces were detected in the photos")
        else:
            print(f"\n✅ Event 11 has {photo_count} photos with {embedding_count} face embeddings")
            print("   If search returns no matches, the selfie face doesn't match any faces in this event.")
            print("   Try lowering the threshold from 0.6 to 0.4 or 0.3")
        
        print("\n" + "=" * 70)
        print("ALL EVENTS SUMMARY:")
        print("=" * 70)
        
        result = await db.execute(
            select(
                Event.event_id,
                Event.name,
                func.count(Photo.photo_id.distinct()).label('photos'),
                func.count(FaceEmbedding.embedding_id).label('embeddings')
            )
            .outerjoin(Photo)
            .outerjoin(FaceEmbedding)
            .group_by(Event.event_id)
            .order_by(Event.event_id)
        )
        
        print(f"\n{'ID':<5} {'Name':<25} {'Photos':<10} {'Embeddings'}")
        print("-" * 70)
        for evt_id, name, photos, embeddings in result:
            print(f"{evt_id:<5} {name:<25} {photos:<10} {embeddings}")

asyncio.run(diagnose())
