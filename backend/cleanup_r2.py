"""
Clean up all files in R2 bucket.
WARNING: This deletes ALL files in the wedding-photos bucket!
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

import boto3
from app.config import get_settings

def cleanup_r2():
    """Delete all files from R2 bucket."""
    settings = get_settings()
    
    print(f"Connecting to R2 bucket: {settings.R2_BUCKET_NAME}")
    
    # Initialize S3 client for R2
    endpoint_url = f"https://{settings.R2_ACCOUNT_ID}.r2.cloudflarestorage.com"
    s3_client = boto3.client(
        's3',
        endpoint_url=endpoint_url,
        aws_access_key_id=settings.R2_ACCESS_KEY_ID,
        aws_secret_access_key=settings.R2_SECRET_ACCESS_KEY,
        region_name='auto'
    )
    
    # List all objects
    print("Fetching list of objects...")
    try:
        response = s3_client.list_objects_v2(Bucket=settings.R2_BUCKET_NAME)
        
        if 'Contents' not in response:
            print("✓ Bucket is already empty!")
            return
        
        objects = response['Contents']
        print(f"Found {len(objects)} objects to delete")
        
        # Confirm deletion
        confirm = input(f"\n⚠️  Delete ALL {len(objects)} files from {settings.R2_BUCKET_NAME}? (yes/no): ")
        if confirm.lower() != 'yes':
            print("Cancelled.")
            return
        
        # Delete all objects
        for obj in objects:
            key = obj['Key']
            print(f"Deleting: {key}")
            s3_client.delete_object(Bucket=settings.R2_BUCKET_NAME, Key=key)
        
        print(f"\n✓ Deleted {len(objects)} files from R2!")
        print("✓ Bucket is now empty and ready for fresh start!")
        
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    cleanup_r2()
