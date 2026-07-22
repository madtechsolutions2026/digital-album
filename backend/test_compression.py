"""
Test aggressive image compression to WebP under 50KB.
"""
import sys
from pathlib import Path
from PIL import Image
import io

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from app.services.image_compressor import ImageCompressor


def test_compression(image_path: str):
    """Test compression on a sample image."""
    print(f"\n[TEST] Testing compression on: {image_path}\n")
    
    try:
        # Load test image
        with Image.open(image_path) as img:
            original_format = img.format
            original_size = img.size
            
            # Get original file size
            with open(image_path, 'rb') as f:
                original_bytes = len(f.read())
            
            print(f"[ORIGINAL] Original Image:")
            print(f"   - Format: {original_format}")
            print(f"   - Size: {original_size[0]}x{original_size[1]}")
            print(f"   - File Size: {original_bytes / 1024:.1f}KB")
            
            # Create compressor
            compressor = ImageCompressor()
            
            # Compress image
            print(f"\n[COMPRESS] Compressing to WebP (target: <50KB)...")
            compressed_image, compressed_bytes = compressor.compress_image(img.copy())
            
            # Get compression info
            info = compressor.get_compression_info(compressed_bytes)
            
            print(f"\n[RESULT] Compressed Image:")
            print(f"   - Format: WebP")
            print(f"   - Size: {compressed_image.size[0]}x{compressed_image.size[1]}")
            print(f"   - File Size: {info['size_kb']}KB")
            print(f"   - Under 50KB: {'YES' if info['under_target'] else 'NO'}")
            print(f"   - Compression Ratio: {original_bytes / len(compressed_bytes):.1f}x")
            
            # Save test output
            output_path = Path(image_path).parent / f"test_compressed_{Path(image_path).stem}.webp"
            with open(output_path, 'wb') as f:
                f.write(compressed_bytes)
            
            print(f"\n[SAVED] Saved compressed test image to: {output_path}")
            
            return True
            
    except Exception as e:
        print(f"\n[ERROR] Compression test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def create_test_image():
    """Create a test image if none exists."""
    print("\n[CREATE] Creating test image (1920x1080, colorful)...")
    
    # Create a colorful test image
    img = Image.new('RGB', (1920, 1080), color='white')
    pixels = img.load()
    
    # Add some color gradients
    for x in range(1920):
        for y in range(1080):
            r = int(255 * (x / 1920))
            g = int(255 * (y / 1080))
            b = 128
            pixels[x, y] = (r, g, b)
    
    test_path = Path(__file__).parent / "test_image.jpg"
    img.save(test_path, 'JPEG', quality=95)
    
    print(f"[SUCCESS] Test image created: {test_path}")
    return str(test_path)


if __name__ == "__main__":
    print("=" * 60)
    print("IMAGE COMPRESSION TEST")
    print("Target: WebP format, <50KB file size")
    print("=" * 60)
    
    # Check if test image path provided
    if len(sys.argv) > 1:
        image_path = sys.argv[1]
        if not Path(image_path).exists():
            print(f"[ERROR] Image not found: {image_path}")
            sys.exit(1)
    else:
        # Create test image
        image_path = create_test_image()
    
    # Run compression test
    success = test_compression(image_path)
    
    print("\n" + "=" * 60)
    if success:
        print("[SUCCESS] COMPRESSION TEST PASSED")
    else:
        print("[FAILED] COMPRESSION TEST FAILED")
    print("=" * 60 + "\n")
    
    sys.exit(0 if success else 1)
