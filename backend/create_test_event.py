"""
Quick script to create a test event in the database.
Run this before uploading photos.
"""

import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from app.models.event import Event
from app.config import get_settings

async def create_test_event():
    """Create a test wedding event."""
    settings = get_settings()
    
    # Create async engine
    engine = create_async_engine(
        settings.DATABASE_URL,
        echo=True
    )
    
    # Create session
    async_session = sessionmaker(
        engine, 
        class_=AsyncSession, 
        expire_on_commit=False
    )
    
    async with async_session() as session:
        # Check if event already exists
        from sqlalchemy import select
        result = await session.execute(
            select(Event).where(Event.event_id == 1)
        )
        existing_event = result.scalar_one_or_none()
        
        if existing_event:
            print(f"✅ Event already exists:")
            print(f"   ID: {existing_event.event_id}")
            print(f"   Name: {existing_event.name}")
            print(f"   Date: {existing_event.event_date}")
            return
        
        # Create new event
        from datetime import datetime
        event = Event(
            name="Test Wedding Event",
            event_date=datetime(2026, 7, 21, 14, 0, 0)
        )
        
        session.add(event)
        await session.commit()
        await session.refresh(event)
        
        print(f"✅ Event created successfully!")
        print(f"   ID: {event.event_id}")
        print(f"   Name: {event.name}")
        print(f"   Date: {event.event_date}")
    
    await engine.dispose()

if __name__ == "__main__":
    print("Creating test event...")
    asyncio.run(create_test_event())
    print("\n✨ You can now upload photos with event_id=1")
