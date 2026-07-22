"""
Cleanup script to delete all events, photos, and face embeddings from database and R2.
"""
import asyncio
import boto3
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import async_session_maker
from app.models import Event, Photo, FaceEmbedding
from app.config import get_settings


async def cleanup_database():
    """Delete all data from database tables."""
    print("🗑️  Cleaning up database...")
    
    async with async_session_maker() as db:
        # Delete face embeddings first (foreign key constraint)
        result = await db.execute(delete(FaceEmbedding))
        face_count = result.rowcount
        print(f"   ✓ Deleted {face_count} face embeddings")
        
        # Delete photos
        result = await db.execute(delete(Photo))
        photo_count = result.rowcount
        print(f"   ✓ Deleted {photo_count} photos")
        
        # Delete events
        result = await db.execute(delete(Event))
        event_count = result.rowcount
        print(f"   ✓ Deleted {event_count} events")
        
        await db.commit()
        print("✅ Database cleanup complete!")
        
        return event_count, photo_count, face_count


async def cleanup_r2():
    """Delete all objects from Cloudflare R2 bucket."""
    print("\n🗑️  Cleaning up Cloudflare R2...")
    
    settings = get_settings()
    
    if settings.STORAGE_TYPE != "r2":
        print("   ⚠️  Storage type is not R2, skipping...")
        return 0
    
    # Initialize R2 client
    s3_client = boto3.client(
        's3',
        endpoint_url=f'https://{settings.R2_ACCOUNT_ID}.r2.cloudflarestorage.com',
        aws_access_key_id=settings.R2_ACCESS_KEY_ID,
        aws_secret_access_key=settings.R2_SECRET_ACCESS_KEY,
        region_name='auto'
    )
    
    try:
        # List all objects
        bucket_name = settings.R2_BUCKET_NAME
        response = s3_client.list_objects_v2(Bucket=bucket_name)
        
        if 'Contents' not in response:
            print("   ✓ R2 bucket is already empty")
            return 0
        
        # Delete all objects
        objects_to_delete = [{'Key': obj['Key']} for obj in response['Contents']]
        
        if objects_to_delete:
            s3_client.delete_objects(
                Bucket=bucket_name,
                Delete={'Objects': objects_to_delete}
            )
            count = len(objects_to_delete)
            print(f"   ✓ Deleted {count} objects from R2")
            
            # Handle pagination if there are more than 1000 objects
            while response.get('IsTruncated', False):
                response = s3_client.list_objects_v2(
                    Bucket=bucket_name,
                    ContinuationToken=response['NextContinuationToken']
                )
                
                if 'Contents' in response:
                    objects_to_delete = [{'Key': obj['Key']} for obj in response['Contents']]
                    s3_client.delete_objects(
                        Bucket=bucket_name,
                        Delete={'Objects': objects_to_delete}
                    )
                    count += len(objects_to_delete)
                    print(f"   ✓ Deleted {len(objects_to_delete)} more objects from R2")
            
            print(f"✅ R2 cleanup complete! Total deleted: {count}")
            return count
        else:
            print("   ✓ R2 bucket is already empty")
            return 0
            
    except Exception as e:
        print(f"   ❌ Error cleaning up R2: {str(e)}")
        return 0


async def main():
    """Run full cleanup."""
    print("=" * 60)
    print("🧹 CLEANUP SCRIPT - DELETE ALL DATA")
    print("=" * 60)
    print("\nThis will delete:")
    print("  • All events from database")
    print("  • All photos from database")
    print("  • All face embeddings from database")
    print("  • All files from Cloudflare R2")
    print("\n⚠️  THIS CANNOT BE UNDONE! ⚠️\n")
    
    confirm = input("Type 'DELETE ALL' to confirm: ")
    
    if confirm != "DELETE ALL":
        print("\n❌ Cleanup cancelled")
        return
    
    print("\n🚀 Starting cleanup...\n")
    
    # Cleanup database
    event_count, photo_count, face_count = await cleanup_database()
    
    # Cleanup R2
    r2_count = await cleanup_r2()
    
    print("\n" + "=" * 60)
    print("✅ CLEANUP COMPLETE!")
    print("=" * 60)
    print(f"\nSummary:")
    print(f"  • Events deleted: {event_count}")
    print(f"  • Photos deleted: {photo_count}")
    print(f"  • Face embeddings deleted: {face_count}")
    print(f"  • R2 objects deleted: {r2_count}")
    print("\n🎉 Database and R2 are now clean! Ready for fresh testing.\n")


if __name__ == "__main__":
    asyncio.run(main())
