"""
Aggressive image compression service for WebP format.

This module compresses images to under 200KB while maintaining reasonable quality.
"""

import io
import logging
from typing import Tuple
from PIL import Image

from app.exceptions import ValidationError


class ImageCompressor:
    """
    Service for aggressively compressing images to WebP format under 200KB.
    
    Strategy:
    1. Convert to WebP format (best compression)
    2. Resize if needed to reduce file size
    3. Reduce quality iteratively until under 200KB
    4. Maintain reasonable visual quality
    """
    
    TARGET_SIZE_KB = 200
    TARGET_SIZE_BYTES = TARGET_SIZE_KB * 1024
    MIN_QUALITY = 20
    # Start the quality search at 80, not 90. A 1920px WebP at q90 lands right
    # on the 200KB target, so detailed photos failed the first attempt and paid
    # a second (often third) full re-encode - ~1s each - to discover what q80
    # gives immediately. Starting here makes almost every photo a single encode.
    MAX_QUALITY = 80
    QUALITY_STEP = 10
    MAX_DIMENSION = 1920  # Start with reasonable size
    
    def __init__(self):
        """Initialize the image compressor."""
        self.logger = logging.getLogger(__name__)
    
    def compress_image(self, image: Image.Image) -> Tuple[Image.Image, bytes]:
        """
        Compress image to under 200KB as WebP.
        
        Strategy:
        1. Try with original size at various qualities
        2. If still too large, progressively resize
        3. Return compressed image and bytes
        
        Args:
            image: PIL Image object (already validated)
            
        Returns:
            Tuple of (processed_image, compressed_bytes)
            
        Raises:
            ValidationError: If compression fails
        """
        try:
            # Convert to RGB if needed (WebP doesn't support all modes well)
            if image.mode not in ('RGB', 'RGBA'):
                if image.mode == 'P' and 'transparency' in image.info:
                    image = image.convert('RGBA')
                else:
                    image = image.convert('RGB')

            # Resize to a sane max dimension before ever attempting a quality
            # search. A full-resolution photo (12MP+) almost never fits the
            # target size anyway, so encoding it repeatedly at full size (once
            # per quality level tried) wastes most of the compression time for
            # nothing - resizing first cuts encode cost proportionally to the
            # pixel count reduction.
            if max(image.size) > self.MAX_DIMENSION:
                image = self._resize_image(image, self.MAX_DIMENSION)

            # Try compression at current size
            result = self._compress_at_size(image, image.size)
            if result:
                processed_image, compressed_bytes = result
                self.logger.info(
                    f"Image compressed successfully: {len(compressed_bytes) / 1024:.1f}KB "
                    f"(size: {processed_image.size})"
                )
                return processed_image, compressed_bytes
            
            # If still too large, progressively resize
            current_dimension = min(image.size)
            resize_steps = [1600, 1280, 1024, 800, 640, 512, 400, 320]
            
            for max_dim in resize_steps:
                if max_dim >= current_dimension:
                    continue
                
                resized_image = self._resize_image(image, max_dim)
                result = self._compress_at_size(resized_image, resized_image.size)
                
                if result:
                    processed_image, compressed_bytes = result
                    self.logger.info(
                        f"Image compressed with resize: {len(compressed_bytes) / 1024:.1f}KB "
                        f"(size: {processed_image.size})"
                    )
                    return processed_image, compressed_bytes
            
            # Last resort: very small size with minimum quality
            tiny_image = self._resize_image(image, 256)
            compressed_bytes = self._compress_webp(tiny_image, quality=self.MIN_QUALITY)
            
            self.logger.warning(
                f"Used aggressive compression: {len(compressed_bytes) / 1024:.1f}KB "
                f"(size: {tiny_image.size}, quality: {self.MIN_QUALITY})"
            )
            
            return tiny_image, compressed_bytes
            
        except Exception as e:
            self.logger.error(f"Image compression failed: {str(e)}", exc_info=True)
            raise ValidationError(f"Failed to compress image: {str(e)}")
    
    def _compress_at_size(
        self, 
        image: Image.Image, 
        size: Tuple[int, int]
    ) -> Tuple[Image.Image, bytes] | None:
        """
        Try to compress image at given size with varying quality.
        
        Args:
            image: PIL Image object
            size: Target size (width, height)
            
        Returns:
            Tuple of (image, bytes) if successful, None if too large
        """
        # Try different quality levels
        for quality in range(self.MAX_QUALITY, self.MIN_QUALITY - 1, -self.QUALITY_STEP):
            compressed_bytes = self._compress_webp(image, quality=quality)
            
            if len(compressed_bytes) <= self.TARGET_SIZE_BYTES:
                return (image, compressed_bytes)
        
        return None
    
    def _compress_webp(self, image: Image.Image, quality: int) -> bytes:
        """
        Compress image to WebP format.
        
        Args:
            image: PIL Image object
            quality: WebP quality (0-100)
            
        Returns:
            Compressed image bytes
        """
        output = io.BytesIO()
        
        # WebP compression parameters
        save_kwargs = {
            'format': 'WEBP',
            'quality': quality,
            # method=2 encodes ~2x faster than method=4 for a few percent more
            # bytes. Encode time is the upload bottleneck and we have headroom
            # under the 200KB target, so trade size for speed.
            'method': 2,
            'lossless': False
        }
        
        # For RGBA images, handle transparency
        if image.mode == 'RGBA':
            # Check if actually has transparency
            if image.getchannel('A').getextrema() == (255, 255):
                # No transparency, convert to RGB
                rgb_image = Image.new('RGB', image.size, (255, 255, 255))
                rgb_image.paste(image, mask=image.split()[3])
                rgb_image.save(output, **save_kwargs)
            else:
                # Has transparency, keep RGBA
                image.save(output, **save_kwargs)
        else:
            image.save(output, **save_kwargs)
        
        return output.getvalue()
    
    def _resize_image(self, image: Image.Image, max_dimension: int) -> Image.Image:
        """
        Resize image maintaining aspect ratio.
        
        Args:
            image: PIL Image object
            max_dimension: Maximum width or height
            
        Returns:
            Resized image
        """
        width, height = image.size
        
        if width <= max_dimension and height <= max_dimension:
            return image
        
        # Calculate new size maintaining aspect ratio
        if width > height:
            new_width = max_dimension
            new_height = int(height * (max_dimension / width))
        else:
            new_height = max_dimension
            new_width = int(width * (max_dimension / height))
        
        # Use LANCZOS for high-quality downsampling
        resized = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
        
        self.logger.debug(f"Resized image from {image.size} to {resized.size}")
        
        return resized
    
    def get_compression_info(self, compressed_bytes: bytes) -> dict:
        """
        Get information about compressed image.
        
        Args:
            compressed_bytes: Compressed image bytes
            
        Returns:
            Dictionary with compression info
        """
        size_kb = len(compressed_bytes) / 1024
        
        return {
            'size_bytes': len(compressed_bytes),
            'size_kb': round(size_kb, 2),
            'under_target': size_kb <= self.TARGET_SIZE_KB,
            'target_kb': self.TARGET_SIZE_KB
        }
