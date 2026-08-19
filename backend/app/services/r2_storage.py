"""
Cloudflare R2 storage service for uploaded images.

This module handles image storage to Cloudflare R2 (S3-compatible object storage).
"""

import io
import uuid
import logging
from typing import Optional
from PIL import Image
import boto3
from botocore.exceptions import ClientError

from app.config import get_settings
from app.exceptions import ValidationError
from app.services.image_compressor import ImageCompressor


class R2StorageService:
    """
    Service for storing and managing uploaded images in Cloudflare R2.
    
    Features:
    - S3-compatible API via boto3
    - Event-specific prefixes (folders)
    - UUID-based filenames
    - Public URL generation
    """
    
    def __init__(self):
        """Initialize R2 storage service with credentials from settings."""
        self.settings = get_settings()
        self.logger = logging.getLogger(__name__)
        self.compressor = ImageCompressor()
        
        # Validate R2 configuration
        if not all([
            self.settings.R2_ACCOUNT_ID,
            self.settings.R2_ACCESS_KEY_ID,
            self.settings.R2_SECRET_ACCESS_KEY,
            self.settings.R2_BUCKET_NAME
        ]):
            raise ValueError(
                "R2 storage requires R2_ACCOUNT_ID, R2_ACCESS_KEY_ID, "
                "R2_SECRET_ACCESS_KEY, and R2_BUCKET_NAME to be configured"
            )
        
        # R2 endpoint URL
        endpoint_url = f"https://{self.settings.R2_ACCOUNT_ID}.r2.cloudflarestorage.com"
        
        # Initialize S3 client for R2
        self.s3_client = boto3.client(
            's3',
            endpoint_url=endpoint_url,
            aws_access_key_id=self.settings.R2_ACCESS_KEY_ID,
            aws_secret_access_key=self.settings.R2_SECRET_ACCESS_KEY,
            region_name='auto'  # R2 uses 'auto' region
        )
        
        self.bucket_name = self.settings.R2_BUCKET_NAME
        
        # Determine public URL base
        if self.settings.R2_PUBLIC_URL:
            self.public_url_base = self.settings.R2_PUBLIC_URL.rstrip('/')
        else:
            # R2 public URL doesn't include bucket name in path
            # Format: https://pub-{hash}.r2.dev (without bucket name)
            # The hash is provided by Cloudflare when you enable public access
            # Default format - you should set R2_PUBLIC_URL in .env with the actual URL
            self.public_url_base = f"https://pub-{self.settings.R2_ACCOUNT_ID}.r2.dev"
        
        self.logger.info(f"R2StorageService initialized for bucket: {self.bucket_name}")
        self.logger.info(f"R2 public URL base: {self.public_url_base}")
    
    def save_image(
        self,
        image: Image.Image,
        event_id: int,
        event_name: str,
        format: str = "WEBP",  # Force WebP for compression
        original_filename: Optional[str] = None
    ) -> str:
        """
        Save an image to R2 storage with aggressive compression to <50KB WebP.
        
        Args:
            image: PIL Image object to save
            event_id: ID of the event this image belongs to
            event_name: Name of the event (used for folder name)
            format: Image format (always WEBP for compression)
            original_filename: Original filename (used for logging only)
            
        Returns:
            Full public URL to the image in R2
            
        Raises:
            ValidationError: If saving fails
        """
        try:
            # Always use WebP for best compression
            format = "WEBP"

            key = self._build_key(event_name)
            folder_name = key.split('/')[0]
            
            # Compress image to under 50KB
            processed_image, compressed_bytes = self.compressor.compress_image(image)
            
            # Upload to R2
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=key,
                Body=compressed_bytes,
                ContentType='image/webp',
                CacheControl='public, max-age=31536000'  # 1 year cache
            )
            
            compression_info = self.compressor.get_compression_info(compressed_bytes)
            
            # Return full public URL
            public_url = self.get_public_url(key)
            
            self.logger.info(
                f"Image uploaded to R2: {key} ({compression_info['size_kb']}KB)",
                extra={
                    "key": key,
                    "event_id": event_id,
                    "event_name": event_name,
                    "folder_name": folder_name,
                    "format": format,
                    "original_filename": original_filename,
                    "compressed_size_kb": compression_info['size_kb'],
                    "image_dimensions": processed_image.size,
                    "public_url": public_url
                }
            )
            
            return public_url
            
        except ClientError as e:
            self.logger.error(
                f"Failed to upload to R2: {str(e)}",
                exc_info=True,
                extra={
                    "event_id": event_id,
                    "event_name": event_name,
                    "original_filename": original_filename
                }
            )
            raise ValidationError(f"Failed to upload image: {str(e)}")
        except Exception as e:
            self.logger.error(
                f"Unexpected error uploading to R2: {str(e)}",
                exc_info=True
            )
            raise ValidationError(f"Failed to upload image: {str(e)}")
    
    def save_bytes(
        self,
        data: bytes,
        event_id: int,
        event_name: str,
        original_filename: Optional[str] = None
    ) -> str:
        """
        Upload already-encoded WebP bytes to R2 without touching the pixels.

        Used for the passthrough path, where the browser has already produced a
        file that meets our size and dimension limits (see
        ImageValidator.try_passthrough). Skips the decode/compress work that
        save_image does.

        Args:
            data: Encoded WebP bytes to store verbatim
            event_id: ID of the event this image belongs to
            event_name: Name of the event (used for folder name)
            original_filename: Original filename (used for logging only)

        Returns:
            Full public URL to the image in R2

        Raises:
            ValidationError: If the upload fails
        """
        try:
            key = self._build_key(event_name)

            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=key,
                Body=data,
                ContentType='image/webp',
                CacheControl='public, max-age=31536000'  # 1 year cache
            )

            public_url = self.get_public_url(key)

            self.logger.info(
                f"Image stored as-is in R2: {key} ({len(data) / 1024:.1f}KB, no re-encode)",
                extra={
                    "key": key,
                    "event_id": event_id,
                    "event_name": event_name,
                    "original_filename": original_filename,
                    "compressed_size_kb": round(len(data) / 1024, 2),
                    "passthrough": True,
                    "public_url": public_url
                }
            )

            return public_url

        except ClientError as e:
            self.logger.error(
                f"Failed to upload to R2: {str(e)}",
                exc_info=True,
                extra={"event_id": event_id, "event_name": event_name}
            )
            raise ValidationError(f"Failed to upload image: {str(e)}")

    def _build_key(self, event_name: str) -> str:
        """
        Build the object key (folder + unique filename) for an event's image.

        Args:
            event_name: Name of the event, used as the folder

        Returns:
            Object key, e.g. "john-wedding/1f3c....webp"
        """
        # Sanitize event name for folder name (lowercase, spaces to hyphens)
        folder_name = event_name.lower().replace(' ', '-').replace('_', '-')
        # Remove special characters
        folder_name = ''.join(c for c in folder_name if c.isalnum() or c == '-')

        return f"{folder_name}/{uuid.uuid4()}.webp"

    def get_public_url(self, key: str) -> str:
        """
        Get public URL for an object in R2.
        
        Args:
            key: Object key in R2 (e.g., "event_1/abc123.jpg")
            
        Returns:
            Public URL for the object
        """
        return f"{self.public_url_base}/{key}"
    
    def delete_file(self, key: str) -> bool:
        """
        Delete a file from R2.
        
        Args:
            key: Object key in R2
            
        Returns:
            True if file was deleted, False if file didn't exist
            
        Raises:
            ValidationError: If deletion fails
        """
        try:
            self.s3_client.delete_object(
                Bucket=self.bucket_name,
                Key=key
            )
            self.logger.info(f"File deleted from R2: {key}")
            return True
            
        except ClientError as e:
            if e.response['Error']['Code'] == 'NoSuchKey':
                self.logger.warning(f"File not found in R2: {key}")
                return False
            else:
                self.logger.error(
                    f"Failed to delete from R2: {str(e)}",
                    exc_info=True,
                    extra={"key": key}
                )
                raise ValidationError(f"Failed to delete file: {str(e)}")
    
    def file_exists(self, key: str) -> bool:
        """
        Check if a file exists in R2.
        
        Args:
            key: Object key in R2
            
        Returns:
            True if file exists, False otherwise
        """
        try:
            self.s3_client.head_object(
                Bucket=self.bucket_name,
                Key=key
            )
            return True
        except ClientError:
            return False
    
    def _get_extension_for_format(self, format: str) -> str:
        """
        Get file extension for image format.
        
        Args:
            format: Image format (JPEG, PNG, WEBP)
            
        Returns:
            File extension with dot (e.g., ".jpg")
        """
        format_map = {
            "JPEG": ".jpg",
            "PNG": ".png",
            "WEBP": ".webp"
        }
        return format_map.get(format.upper(), ".jpg")


# Global singleton instance. Constructing R2StorageService creates a new
# boto3 S3 client (and connection pool), which costs real time (~1s) and
# throws away connection keep-alive if rebuilt on every request.
_r2_storage_service: Optional["R2StorageService"] = None


def get_r2_storage_service() -> "R2StorageService":
    """
    Get or create the global R2StorageService instance.

    Ensures the boto3 client and its connection pool are created once and
    reused across requests, instead of once per upload.

    Returns:
        R2StorageService instance
    """
    global _r2_storage_service

    if _r2_storage_service is None:
        _r2_storage_service = R2StorageService()

    return _r2_storage_service
