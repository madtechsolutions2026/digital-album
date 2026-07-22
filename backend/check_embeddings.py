"""
Quick script to check if face embeddings exist in the database.
"""
import asyncio
from sqlalchemy import select, func
from app.database import async_session_maker
from app.models import Event, Photo, FaceEmbedding

async def check_data():
    async with async_session_maker() as db:
        # Count events
        result = await db.execute(select(func.count(Event.event_id)))
        event_count = result.scalar()
        
        # Count photos
        result = await db.execute(select(func.count(Photo.photo_id)))
        photo_count = result.scalar()
        
        # Count face embeddings
        result = await db.execute(select(func.count(FaceEmbedding.embedding_id)))
        embedding_count = result.scalar()
        
        print("=" * 60)
        print("DATABASE STATUS")
        print("=" * 60)
        print(f"\n📅 Events: {event_count}")
        print(f"🖼️  Photos: {photo_count}")
        print(f"👤 Face Embeddings: {embedding_count}")
        
        if photo_count > 0 and embedding_count == 0:
            print("\n⚠️  WARNING: You have photos but NO face embeddings!")
            print("   This means face processing hasn't run yet.")
            
        # Show photos without embeddings
        result = await db.execute(
            select(Photo.photo_id, Photo.filename, Event.name)
            .join(Event)
            .outerjoin(FaceEmbedding)
            .group_by(Photo.photo_id, Event.name)
            .having(func.count(FaceEmbedding.embedding_id) == 0)
        )
        photos_without_embeddings = result.all()
        
        if photos_without_embeddings:
            print(f"\n❌ Photos WITHOUT face embeddings: {len(photos_without_embeddings)}")
            for photo_id, filename, event_name in photos_without_embeddings[:5]:
                print(f"   - Photo {photo_id} ({filename}) in event '{event_name}'")
        else:
            print("\n✅ All photos have face embeddings!")
        
        print("\n" + "=" * 60)

asyncio.run(check_data())
