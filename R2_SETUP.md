# Cloudflare R2 Storage Setup Guide

## Why Cloudflare R2?

✅ **Zero egress fees** - No bandwidth charges for downloads  
✅ **S3-compatible** - Works with existing S3 tools  
✅ **Fast CDN** - Global distribution  
✅ **Cost-effective** - ~$0.015/GB storage  

## Step 1: Create Cloudflare R2 Bucket

1. Go to [Cloudflare Dashboard](https://dash.cloudflare.com/)
2. Navigate to **R2 Storage** in the left sidebar
3. Click **Create bucket**
4. Enter bucket name: `wedding-photos` (or your preferred name)
5. Click **Create bucket**

## Step 2: Get R2 Credentials

### Get Account ID
1. In R2 dashboard, you'll see your **Account ID** at the top
2. Copy this ID (looks like: `a1b2c3d4e5f6g7h8i9j0`)

### Create API Token
1. Click **Manage R2 API Tokens**
2. Click **Create API token**
3. Name: `wedding-photos-api`
4. Permissions: **Admin Read & Write**
5. Click **Create API token**
6. **IMPORTANT**: Copy both:
   - Access Key ID
   - Secret Access Key
   (You can't see the secret again!)

## Step 3: Configure Backend

### Install boto3
```bash
cd backend
.\venv\Scripts\Activate.ps1
pip install boto3
```

### Update .env file
```env
# Storage Configuration
STORAGE_TYPE=r2  # Change from 'local' to 'r2'

# Cloudflare R2 Configuration
R2_ACCOUNT_ID=your_account_id_here
R2_ACCESS_KEY_ID=your_access_key_id_here
R2_SECRET_ACCESS_KEY=your_secret_access_key_here
R2_BUCKET_NAME=wedding-photos
R2_PUBLIC_URL=  # Leave empty for now
```

## Step 4: Make Bucket Public (Optional)

If you want photos to be publicly accessible:

1. Go to your bucket settings
2. Click **Settings** tab
3. Under **Public Access**, enable **Allow Access**
4. Your public URL will be: `https://pub-{account_id}.r2.dev/wedding-photos`

### For Custom Domain (Advanced)
1. Add custom domain in bucket settings
2. Set up DNS CNAME record
3. Update `.env`:
   ```env
   R2_PUBLIC_URL=https://photos.yourdomain.com
   ```

## Step 5: Test Upload

1. Restart backend server
2. Upload a test photo via `/admin`
3. Check if it appears in R2 dashboard
4. Try viewing it in gallery

## Step 6: Migrate Existing Photos (If Any)

If you have existing local photos, you can migrate them:

### Option A: Manual Upload
1. Download photos from `backend/storage/photos/`
2. Upload to R2 via dashboard

### Option B: Script Migration (TODO)
We can create a migration script if needed.

## Frontend Changes

The frontend automatically works with R2! The backend now returns R2 URLs:
- Local: `http://localhost:8000/storage/event_1/file.jpg`
- R2: `https://pub-xxx.r2.dev/wedding-photos/event_1/file.jpg`

## Switching Between Local and R2

Change `STORAGE_TYPE` in `.env`:
- `STORAGE_TYPE=local` - Uses local filesystem
- `STORAGE_TYPE=r2` - Uses Cloudflare R2

No code changes needed!

## Cost Estimate

For a wedding photography business:
- Storage: 100GB = **$1.50/month**
- Operations: 1M requests = **$4.50/month**
- Bandwidth: **$0** (zero egress fees!)

Total: **~$6/month** for substantial usage

## Troubleshooting

### "R2 storage not configured properly"
- Check all R2 credentials are in `.env`
- Verify account ID is correct
- Ensure API token has Admin permissions

### Images not loading
- Check bucket is set to public access
- Verify public URL in bucket settings
- Check CORS settings in R2 dashboard

### Upload fails
- Verify API token hasn't expired
- Check bucket name matches exactly
- Ensure bucket exists in the account

## Security Best Practices

✅ **Never commit** R2 credentials to git  
✅ **Use environment variables** only  
✅ **Rotate API tokens** periodically  
✅ **Set bucket policies** to restrict access  
✅ **Enable access logs** for monitoring  

## Production Checklist

- [ ] R2 bucket created
- [ ] API tokens generated
- [ ] `.env` configured with R2 credentials
- [ ] boto3 installed
- [ ] Public access enabled (if needed)
- [ ] Custom domain configured (optional)
- [ ] Test upload working
- [ ] Test download working
- [ ] Gallery loading images
- [ ] Backup strategy defined

## Need Help?

Check Cloudflare R2 docs: https://developers.cloudflare.com/r2/
