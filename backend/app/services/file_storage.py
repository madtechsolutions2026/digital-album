"""
File storage service for uploaded images.

This module handles secure storage of uploaded image files with:
- Event-specific subdirectories
- UUID-based filenames to prevent conflicts
- Filename sanitization to prevent directory traversal
- Path resolution utilities
"""

import os
import uuid
import logging
from pathlib import Path
from typing import Optional

from PIL import Image

from app.config import get_settings
from app.exceptions import ValidationError
from app.services.image_compressor import ImageCompressor


class FileStorageService:
    """
    Service for storing and managing uploaded image files.
    
    Features:
    - Creates event-specific subdirectories
    - Generates unique UUID-based filenames
    - Sanitizes filenames to prevent security issues
    - Provides path resolution utilities
    """
    
    def __init__(self, storage_path: Optional[str] = None):
        """
        Initialize the file storage service.
        
        Args:
            storage_path: Optional custom storage path. If not provided,
                         uses STORAGE_PATH from settings.
        """
        self.settings = get_settings()
        self.logger = logging.getLogger(__name__)
        self.compressor = ImageCompressor()
        
        # Use provided path or default from settings
        if storage_path:
            self.base_path = Path(storage_path)
        else:
            self.base_path = Path(self.settings.STORAGE_PATH)
        
        # Create base storage directory if it doesn't exist
        self._ensure_directory_exists(self.base_path)
        
        self.logger.info(f"FileStorageService initialized with base path: {self.base_path}")
    
    def save_image(
        self,
        image: Image.Image,
        event_id: int,
        event_name: str,
        format: str = "WEBP",  # Force WebP for compression
        original_filename: Optional[str] = None
    ) -> str:
        """
        Save an image to disk with aggressive compression to <50KB WebP.
        
        Creates directory structure: {base_path}/{event-name}/{uuid}.webp
        
        Args:
            image: PIL Image object to save
            event_id: ID of the event this image belongs to
            event_name: Name of the event (used for folder name)
            format: Image format (always WEBP for compression)
            original_filename: Original filename (used for logging only)
            
        Returns:
            Relative path to the saved file (e.g., "john-wedding/abc123.webp")
            
        Raises:
            ValidationError: If saving fails
        """
        # Sanitize event name for folder name (lowercase, replace spaces with hyphens)
        folder_name = event_name.lower().replace(' ', '-').replace('_', '-')
        # Remove special characters
        folder_name = ''.join(c for c in folder_name if c.isalnum() or c == '-')
        
        # Create event-specific subdirectory
        event_dir = self.base_path / folder_name
        self._ensure_directory_exists(event_dir)
        
        # Always use WebP for best compression
        format = "WEBP"
        file_extension = ".webp"
        
        # Generate unique filename
        filename = f"{uuid.uuid4()}{file_extension}"
        
        # Sanitize filename (extra safety, though UUID should be safe)
        filename = self._sanitize_filename(filename)
        
        # Full path to save the file
        full_path = event_dir / filename
        
        # Relative path for database storage
        relative_path = f"{folder_name}/{filename}"
        
        # Compress image to under 50KB
        try:
            processed_image, compressed_bytes = self.compressor.compress_image(image)
            
            # Write compressed bytes to file
            with open(full_path, 'wb') as f:
                f.write(compressed_bytes)
            
            compression_info = self.compressor.get_compression_info(compressed_bytes)
            
            self.logger.info(
                f"Image saved: {relative_path} ({compression_info['size_kb']}KB)",
                extra={
                    "relative_path": relative_path,
                    "event_id": event_id,
                    "event_name": event_name,
                    "folder_name": folder_name,
                    "format": format,
                    "original_filename": original_filename,
                    "compressed_size_kb": compression_info['size_kb'],
                    "image_dimensions": processed_image.size
                }
            )
            
        except Exception as e:
            self.logger.error(
                f"Failed to save image: {str(e)}",
                exc_info=True,
                extra={
                    "event_id": event_id,
                    "event_name": event_name,
                    "filename": filename,
                    "original_filename": original_filename
                }
            )
            raise ValidationError(f"Failed to save image: {str(e)}")
        
        return relative_path
    
    def get_full_path(self, relative_path: str) -> Path:
        """
        Convert relative path to absolute path.
        
        Validates that the path is within the storage directory
        to prevent directory traversal attacks.
        
        Args:
            relative_path: Relative path from the database (e.g., "event_1/abc123.jpg")
            
        Returns:
            Absolute Path object
            
        Raises:
            ValidationError: If path is invalid or outside storage directory
        """
        # Sanitize the relative path
        relative_path = self._sanitize_path(relative_path)
        
        # Resolve to absolute path
        full_path = (self.base_path / relative_path).resolve()
        
        # Ensure the path is within the base storage directory
        try:
            full_path.relative_to(self.base_path.resolve())
        except ValueError:
            raise ValidationError(
                "Invalid file path: path is outside storage directory"
            )
        
        return full_path
    
    def file_exists(self, relative_path: str) -> bool:
        """
        Check if a file exists at the given relative path.
        
        Args:
            relative_path: Relative path from the database
            
        Returns:
            True if file exists, False otherwise
        """
        try:
            full_path = self.get_full_path(relative_path)
            return full_path.exists() and full_path.is_file()
        except ValidationError:
            return False
    
    def delete_file(self, relative_path: str) -> bool:
        """
        Delete a file at the given relative path.
        
        Args:
            relative_path: Relative path from the database
            
        Returns:
            True if file was deleted, False if file didn't exist
            
        Raises:
            ValidationError: If deletion fails
        """
        try:
            full_path = self.get_full_path(relative_path)
            
            if not full_path.exists():
                self.logger.warning(f"File not found for deletion: {relative_path}")
                return False
            
            full_path.unlink()
            self.logger.info(f"File deleted: {relative_path}")
            return True
            
        except Exception as e:
            self.logger.error(
                f"Failed to delete file: {str(e)}",
                exc_info=True,
                extra={"relative_path": relative_path}
            )
            raise ValidationError(f"Failed to delete file: {str(e)}")
    
    def _ensure_directory_exists(self, directory: Path) -> None:
        """
        Create directory if it doesn't exist.
        
        Args:
            directory: Path to directory
        """
        directory.mkdir(parents=True, exist_ok=True)
    
    def _sanitize_filename(self, filename: str) -> str:
        """
        Sanitize filename to prevent directory traversal and other attacks.
        
        Removes:
        - Path separators (/, \\)
        - Parent directory references (..)
        - Null bytes
        
        Args:
            filename: Original filename
            
        Returns:
            Sanitized filename
        """
        # Remove any path separators and parent references
        filename = os.path.basename(filename)
        
        # Remove null bytes
        filename = filename.replace('\0', '')
        
        # Remove any remaining path traversal attempts
        filename = filename.replace('..', '')
        filename = filename.replace('/', '')
        filename = filename.replace('\\', '')
        
        # Ensure filename is not empty after sanitization
        if not filename or filename.startswith('.'):
            filename = f"file_{uuid.uuid4()}"
        
        return filename
    
    def _sanitize_path(self, path: str) -> str:
        """
        Sanitize a relative path to prevent directory traversal.
        
        Args:
            path: Relative path
            
        Returns:
            Sanitized path
        """
        # Normalize the path (removes redundant separators and up-level references)
        path = os.path.normpath(path)
        
        # Remove leading path separators
        path = path.lstrip(os.sep).lstrip('/')
        
        # Ensure no absolute path or drive letter (Windows)
        if os.path.isabs(path):
            raise ValidationError("Absolute paths are not allowed")
        
        # Check for parent directory traversal attempts
        if '..' in Path(path).parts:
            raise ValidationError("Path contains parent directory references")
        
        return path
    
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
