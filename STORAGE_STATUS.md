# Storage Integration Status

## ✅ Completed

### Backend Changes
- [x] Added boto3 to requirements.txt
- [x] Created R2StorageService with S3-compatible API
- [x] Updated config.py with R2 settings (STORAGE_TYPE, R2_ACCOUNT_ID, etc.)
- [x] Modified PhotoService to support both local and R2 storage
- [x] Updated photo routes to initialize R2 when configured
- [x] Installed boto3 in virtual environment

### Frontend Changes
- [x] Updated GalleryPage to handle both local and R2 URLs
- [x] Images now check if URL starts with 'http' (R2) or use local path
- [x] Modal view also supports R2 URLs

### Documentation
- [x] Created R2_SETUP.md with complete setup guide
- [x] Updated .env.example with R2 configuration

## 🎯 Current State

**Storage Type**: Local (default)
- Images stored in: `backend/storage/photos/event_1/`
- URLs: `http://localhost:8000/storage/event_1/filename.webp`

## 📋 Next Steps - To Use R2

### 1. Create Cloudflare R2 Bucket
```
1. Go to Cloudflare Dashboard → R2 Storage
2. Create bucket: "wedding-photos"
3. Get Account ID from dashboard
4. Create API token with Admin Read & Write
5. Copy Access Key ID and Secret Access Key
```

### 2. Configure Backend
Edit `backend/.env`:
```env
STORAGE_TYPE=r2  # Change from 'local' to 'r2'

R2_ACCOUNT_ID=your_account_id_here
R2_ACCESS_KEY_ID=your_access_key_here
R2_SECRET_ACCESS_KEY=your_secret_key_here
R2_BUCKET_NAME=wedding-photos
R2_PUBLIC_URL=  # Optional custom domain
```

### 3. Make Bucket Public (Optional)
- Enable "Public Access" in bucket settings
- Or set up custom domain

### 4. Test
- Restart backend server
- Upload photo via `/admin`
- Verify it appears in R2 dashboard
- Check if it loads in `/gallery`

## 🔄 Switching Storage

You can switch between storage types anytime:

**Local Storage**:
```env
STORAGE_TYPE=local
```

**R2 Storage**:
```env
STORAGE_TYPE=r2
```

No code changes needed - backend automatically uses the right service!

## 🔍 How It Works

### Backend Flow
1. PhotoService checks `settings.STORAGE_TYPE`
2. If `r2` → uses R2StorageService → saves to Cloudflare
3. If `local` → uses FileStorageService → saves to disk
4. Returns file path/URL in response

### Frontend Flow
1. GalleryPage receives photo with `file_path`
2. If path starts with `http` → direct URL (R2)
3. Otherwise → prepends `http://localhost:8000/storage/` (local)

### Example Paths
- **Local**: `event_1/abc123.webp` → `http://localhost:8000/storage/event_1/abc123.webp`
- **R2**: `event_1/abc123.jpg` (stored as key) → `https://pub-xxx.r2.dev/wedding-photos/event_1/abc123.jpg`

## 💰 Cost Comparison

### Local Storage (Current)
- Cost: $0
- Bandwidth: Unlimited (self-hosted)
- Scalability: Limited by disk space
- CDN: None
- Backup: Manual

### Cloudflare R2
- Storage: $0.015/GB (~$1.50 for 100GB)
- Bandwidth: $0 egress (FREE downloads!)
- Operations: ~$4.50/month for 1M requests
- CDN: Global edge network included
- Scalability: Unlimited
- Backup: Built-in redundancy

**Total R2 Cost**: ~$6/month for substantial usage

Compare to AWS S3: Would be $30-50/month with bandwidth!

## 🚨 Current Blockers

**None** - System ready to use either storage!

You just need to:
1. Keep using local storage (no action needed), OR
2. Set up R2 credentials to switch to cloud storage

## 📚 Resources

- Full setup guide: `R2_SETUP.md`
- Cloudflare R2 Docs: https://developers.cloudflare.com/r2/
- boto3 S3 API: https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/s3.html

## 🔐 Security Notes

- Never commit R2 credentials to git
- Use `.env` for all secrets
- Rotate API tokens periodically
- Set bucket CORS if accessing from different domains
- Consider bucket policies to restrict access
