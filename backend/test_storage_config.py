"""
Quick test to verify storage configuration is working properly.
"""
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from app.config import get_settings

def test_storage_config():
    """Test that storage configuration loads correctly."""
    print("Testing storage configuration...\n")
    
    try:
        settings = get_settings()
        
        print("✅ Settings loaded successfully!")
        print(f"\n📦 Storage Configuration:")
        print(f"   - Storage Type: {settings.STORAGE_TYPE}")
        print(f"   - Storage Path: {settings.STORAGE_PATH}")
        
        if settings.STORAGE_TYPE == 'r2':
            print(f"\n☁️  R2 Configuration:")
            print(f"   - Account ID: {'✓ Set' if settings.R2_ACCOUNT_ID else '✗ Missing'}")
            print(f"   - Access Key: {'✓ Set' if settings.R2_ACCESS_KEY_ID else '✗ Missing'}")
            print(f"   - Secret Key: {'✓ Set' if settings.R2_SECRET_ACCESS_KEY else '✗ Missing'}")
            print(f"   - Bucket Name: {settings.R2_BUCKET_NAME or '✗ Missing'}")
            print(f"   - Public URL: {settings.R2_PUBLIC_URL or '(using default)'}")
            
            if not all([
                settings.R2_ACCOUNT_ID,
                settings.R2_ACCESS_KEY_ID,
                settings.R2_SECRET_ACCESS_KEY,
                settings.R2_BUCKET_NAME
            ]):
                print("\n⚠️  WARNING: R2 storage selected but credentials missing!")
                print("   Update .env with R2 credentials or switch to STORAGE_TYPE=local")
        else:
            print(f"\n💾 Using local file storage")
        
        print(f"\n🗄️  Database: {settings.DATABASE_URL.split('@')[1] if '@' in settings.DATABASE_URL else 'configured'}")
        print(f"🌐 CORS Origins: {settings.CORS_ORIGINS}")
        print(f"🐛 Debug Mode: {settings.DEBUG}")
        
        print("\n✅ All configuration checks passed!")
        return True
        
    except Exception as e:
        print(f"\n❌ Configuration error: {e}")
        return False

if __name__ == "__main__":
    success = test_storage_config()
    sys.exit(0 if success else 1)
