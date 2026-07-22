"""
Test script to verify Celery is working and face processing task is registered.
"""
import asyncio
from app.celery_app import celery_app
from app.database import async_session_maker
from sqlalchemy import select
from app.models import Event

print("=" * 60)
print("CELERY TEST SCRIPT")
print("=" * 60)

# Test 1: Check if Celery can connect to Redis
print("\n1. Testing Celery connection to Redis...")
try:
    inspect = celery_app.control.inspect()
    active_workers = inspect.active()
    
    if active_workers:
        print(f"   ✅ Celery connected! Active workers: {list(active_workers.keys())}")
    else:
        print("   ❌ No active Celery workers found!")
        print("   Make sure to start worker with: celery -A app.celery_app worker --loglevel=info --pool=solo")
except Exception as e:
    print(f"   ❌ Celery connection failed: {e}")

# Test 2: Check registered tasks
print("\n2. Checking registered tasks...")
registered_tasks = celery_app.tasks.keys()
face_task = 'app.tasks.face_processing.process_faces_task'

print(f"   Total registered tasks: {len(registered_tasks)}")
if face_task in registered_tasks:
    print(f"   ✅ Face processing task is registered: {face_task}")
else:
    print(f"   ❌ Face processing task NOT found!")
    print(f"   Registered tasks: {list(registered_tasks)}")

# Test 3: Get events from database
print("\n3. Fetching events from database...")

async def get_events():
    async with async_session_maker() as db:
        result = await db.execute(select(Event))
        events = result.scalars().all()
        return events

try:
    events = asyncio.run(get_events())
    print(f"   ✅ Found {len(events)} events in database")
    for event in events:
        print(f"      - Event {event.event_id}: {event.name}")
    
    if events:
        # Test 4: Try to queue a task
        print("\n4. Testing task submission...")
        event_id = events[0].event_id
        print(f"   Attempting to queue task for event {event_id}...")
        
        from app.tasks.face_processing import process_faces_task
        task = process_faces_task.delay(event_id)
        
        print(f"   ✅ Task queued successfully!")
        print(f"   Job ID: {task.id}")
        print(f"   Task state: {task.state}")
        print(f"\n   Check task status with:")
        print(f"   GET http://localhost:8000/api/jobs/{task.id}/status")
        
except Exception as e:
    print(f"   ❌ Error: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 60)
print("TEST COMPLETE")
print("=" * 60)
