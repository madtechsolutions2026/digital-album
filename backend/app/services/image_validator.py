"""
Image validation service.

This module provides validation for uploaded image files including:
- File size limits
- Format validation by header inspection
- Dimension limits
- Image resizing for large images
"""

import io
import logging
from typing import Tuple, Optional

import filetype
from PIL import Image

from app.config import get_settings
from app.exceptions import ValidationError
from app.services.image_compressor import ImageCompressor


class ImageValidator:
    """
    Service for validating and preparing uploaded images.
    
    Validates:
    - File size (max 10MB by default)
    - Image format (JPEG, PNG, WEBP) by header inspection
    - Image dimensions (max 8000x8000 by default)
    - Automatically resizes large images for performance
    """
    
    SUPPORTED_FORMATS = {"image/jpeg", "image/png", "image/webp"}
    SUPPORTED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}
    
    def __init__(self):
        """Initialize the image validator with settings."""
        self.settings = get_settings()
        self.logger = logging.getLogger(__name__)
        self.max_file_size = self.settings.MAX_FILE_SIZE
        self.max_dimension = self.settings.MAX_DIMENSION
        self.resize_threshold = self.settings.RESIZE_THRESHOLD
    
    def validate_and_prepare(
        self,
        file_content: bytes,
        filename: str
    ) -> Tuple[Image.Image, str, Tuple[int, int]]:
        """
        Validate and prepare an image for processing.
        
        Performs the following validations and transformations:
        1. Validates file size
        2. Validates format by header inspection (not extension)
        3. Validates dimensions
        4. Resizes image if larger than threshold
        
        Args:
            file_content: Raw bytes of the uploaded file
            filename: Original filename (used for logging only)
            
        Returns:
            Tuple of (PIL Image object, format string, original size tuple)
            
        Raises:
            ValidationError: If any validation fails
        """
        # Validate file size
        file_size = len(file_content)
        if file_size > self.max_file_size:
            size_mb = file_size / (1024 * 1024)
            max_mb = self.max_file_size / (1024 * 1024)
            raise ValidationError(
                f"File size {size_mb:.2f}MB exceeds maximum allowed size of {max_mb:.0f}MB"
            )
        
        if file_size == 0:
            raise ValidationError("File is empty")
        
        # Validate file format by header inspection
        file_type = filetype.guess(file_content)
        if file_type is None:
            raise ValidationError(
                "Unable to determine file type. Please upload a valid image file."
            )
        
        if file_type.mime not in self.SUPPORTED_FORMATS:
            raise ValidationError(
                f"Unsupported image format: {file_type.mime}. "
                f"Supported formats: JPEG, PNG, WEBP"
            )
        
        # Log validation success
        self.logger.debug(
            f"File format validated: {file_type.mime} for {filename}",
            extra={"image_filename": filename, "mime_type": file_type.mime, "size": file_size}
        )
        
        # Load image with PIL
        try:
            image = Image.open(io.BytesIO(file_content))
            image.load()  # Force loading to catch any corruption
        except Exception as e:
            raise ValidationError(f"Failed to load image: {str(e)}")
        
        # Store original dimensions
        original_size = image.size
        width, height = original_size
        
        # Resize if larger than max dimension (before validation check)
        if width > self.max_dimension or height > self.max_dimension:
            self.logger.info(
                f"Image {width}x{height} exceeds max dimension, resizing to fit within {self.max_dimension}px",
                extra={
                    "image_filename": filename,
                    "original_size": original_size
                }
            )
            image = self._resize_to_max_dimension(image, self.max_dimension)
            self.logger.info(
                f"Resized oversized image from {original_size} to {image.size}",
                extra={
                    "image_filename": filename,
                    "original_size": original_size,
                    "new_size": image.size
                }
            )
        
        # Now validate dimensions (should pass after resize)
        width, height = image.size
        if width < 1 or height < 1:
            raise ValidationError("Image dimensions must be at least 1x1 pixel")
        
        # Further resize if larger than processing threshold
        if width > self.resize_threshold or height > self.resize_threshold:
            image = self._resize_image(image, image.size)
            self.logger.info(
                f"Further resized for processing from {width}x{height} to {image.size}",
                extra={
                    "image_filename": filename,
                    "new_size": image.size
                }
            )
        
        # Convert to RGB if necessary (handles RGBA, grayscale, etc.)
        if image.mode not in ("RGB", "L"):
            self.logger.debug(
                f"Converting image from {image.mode} to RGB",
                extra={"image_filename": filename, "original_mode": image.mode}
            )
            # Convert RGBA to RGB with white background
            if image.mode == "RGBA":
                background = Image.new("RGB", image.size, (255, 255, 255))
                background.paste(image, mask=image.split()[3])  # Use alpha channel as mask
                image = background
            else:
                image = image.convert("RGB")
        
        # Return validated image, format, and original size
        format_str = file_type.extension.upper()
        if format_str == "JPG":
            format_str = "JPEG"
        
        return image, format_str, original_size
    
    def try_passthrough(self, file_content: bytes) -> Optional[Tuple[int, int]]:
        """
        Check whether an upload is already exactly what we would have produced,
        so it can go straight to storage without a decode/re-encode round trip.

        The browser already downscales and converts to WebP before uploading
        (see frontend lib/imageResize.js). When that succeeded, re-decoding and
        re-compressing it server-side reproduces a file we already have - which
        was the single largest cost in an upload (~2s of CPU per photo).

        Only the header is read here; the pixel data is never decoded, so this
        costs microseconds rather than seconds.

        Returns:
            (width, height) if the payload can be stored as-is, else None.
            None simply means "take the normal compress path" - it is not an
            error, and callers must always keep that fallback, because
            resizeImageFile() gives up and sends the untouched original
            whenever the browser cannot decode an image.
        """
        # Never trust the client's declared type - sniff the real magic bytes.
        file_type = filetype.guess(file_content)
        if file_type is None or file_type.mime != "image/webp":
            return None

        # Must already be under what the compressor would target, otherwise
        # we would be storing something bigger than our own pipeline allows.
        if len(file_content) > ImageCompressor.TARGET_SIZE_BYTES:
            return None

        # Read dimensions from the header only - Image.open() is lazy and does
        # not touch pixel data until .load() is called, which we deliberately
        # never do on this path.
        try:
            with Image.open(io.BytesIO(file_content)) as image:
                width, height = image.size
        except Exception:
            # Malformed header - fall back to the full validate path, which
            # will produce a proper ValidationError for the client.
            return None

        if width < 1 or height < 1:
            return None

        if max(width, height) > ImageCompressor.MAX_DIMENSION:
            return None

        self.logger.debug(
            f"Upload accepted as-is: {width}x{height} WebP, "
            f"{len(file_content) / 1024:.1f}KB (no server re-encode)"
        )

        return (width, height)

    def _resize_to_max_dimension(
        self,
        image: Image.Image,
        max_dimension: int
    ) -> Image.Image:
        """
        Resize image to fit within max dimension while maintaining aspect ratio.
        
        Args:
            image: PIL Image to resize
            max_dimension: Maximum allowed dimension
            
        Returns:
            Resized PIL Image
        """
        image.thumbnail(
            (max_dimension, max_dimension),
            Image.Resampling.LANCZOS
        )
        return image
    
    def _resize_image(
        self,
        image: Image.Image,
        original_size: Tuple[int, int]
    ) -> Image.Image:
        """
        Resize image while maintaining aspect ratio.
        
        Uses thumbnail() method which maintains aspect ratio and ensures
        neither dimension exceeds the threshold.
        
        Args:
            image: PIL Image to resize
            original_size: Original image dimensions
            
        Returns:
            Resized PIL Image
        """
        # Use thumbnail to maintain aspect ratio
        # It will resize to fit within the box while maintaining aspect ratio
        image.thumbnail(
            (self.resize_threshold, self.resize_threshold),
            Image.Resampling.LANCZOS  # High-quality downsampling
        )
        
        return image
    
    def validate_file_size(self, file_size: int) -> None:
        """
        Validate file size only.
        
        Args:
            file_size: Size of the file in bytes
            
        Raises:
            ValidationError: If file size exceeds maximum
        """
        if file_size > self.max_file_size:
            size_mb = file_size / (1024 * 1024)
            max_mb = self.max_file_size / (1024 * 1024)
            raise ValidationError(
                f"File size {size_mb:.2f}MB exceeds maximum allowed size of {max_mb:.0f}MB"
            )
        
        if file_size == 0:
            raise ValidationError("File is empty")
