"""
Quick script to create a test event in the database.
Run this before uploading photos.
"""

import asyncio
from datetime import datetime
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
    
    test_events = [
        {
            "name": "Arun & Pavithra's Wedding",
            "access_code": "ARUN26",
            "password": "wedding2026",
            "date": datetime(2026, 8, 15, 11, 0, 0)
        },
        {
            "name": "Meera & Rohan's Engagement",
            "access_code": "MEEROH",
            "password": "meerah2026",
            "date": datetime(2026, 9, 2, 16, 0, 0)
        },
        {
            "name": "Sneha & Vijay's Reception",
            "access_code": "SNEVIJ",
            "password": "reception2026",
            "date": datetime(2026, 10, 10, 19, 0, 0)
        }
    ]

    async with async_session() as session:
        from sqlalchemy import select
        from app.services.auth import hash_password

        for te in test_events:
            result = await session.execute(
                select(Event).where(Event.access_code == te["access_code"])
            )
            existing_event = result.scalar_one_or_none()
            
            if existing_event:
                print(f"Event already exists: {te['name']} (Code: {te['access_code']})")
                continue
            
            event = Event(
                name=te["name"],
                event_date=te["date"],
                access_code=te["access_code"],
                password_hash=hash_password(te["password"])
            )
            
            session.add(event)
            await session.commit()
            print(f"Event created successfully: {te['name']} (Code: {te['access_code']}, Password: {te['password']})")
            
    await engine.dispose()

if __name__ == "__main__":
    print("Creating test events...")
    asyncio.run(create_test_event())
    print("\nYou can now upload photos using the generated codes.")
