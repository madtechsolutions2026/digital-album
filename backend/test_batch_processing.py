"""
Test if batch processing API endpoint works.
"""
import asyncio
import httpx

async def test():
    print("=" * 60)
    print("TESTING BATCH PROCESSING API")
    print("=" * 60)
    
    # Step 1: Get events
    print("\n1. Fetching events...")
    async with httpx.AsyncClient() as client:
        response = await client.get("http://localhost:8000/api/events")
        events = response.json()['data']['events']
        
        if not events:
            print("   ❌ No events found! Create an event first.")
            return
        
        print(f"   ✅ Found {len(events)} event(s)")
        for event in events:
            print(f"      - Event {event['event_id']}: {event['name']} ({event['photo_count']} photos)")
        
        # Step 2: Try to trigger batch processing on first event
        event_id = events[0]['event_id']
        print(f"\n2. Triggering batch processing for event {event_id}...")
        
        try:
            response = await client.post(f"http://localhost:8000/api/events/{event_id}/process-faces")
            result = response.json()
            
            if response.status_code == 202:
                print(f"   ✅ Batch processing queued successfully!")
                print(f"      Job ID: {result['data']['job_id']}")
                print(f"      Status URL: {result['data']['status_url']}")
                
                # Step 3: Check job status
                job_id = result['data']['job_id']
                print(f"\n3. Checking job status...")
                
                for i in range(5):
                    await asyncio.sleep(2)
                    response = await client.get(f"http://localhost:8000/api/jobs/{job_id}/status")
                    status = response.json()
                    
                    print(f"   Attempt {i+1}: Status = {status['status']}")
                    
                    if status['status'] in ['success', 'failure']:
                        break
                
                print(f"\n✅ Test complete! Check Celery logs for processing details.")
            else:
                print(f"   ❌ Failed with status {response.status_code}")
                print(f"      Response: {result}")
        
        except Exception as e:
            print(f"   ❌ Error: {e}")
            print(f"   Error type: {type(e).__name__}")
            import traceback
            traceback.print_exc()

print("Make sure:")
print("1. Backend is running (http://localhost:8000)")
print("2. Celery worker is running")
print("3. Redis is running")
print()

asyncio.run(test())
