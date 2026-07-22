# R2 Image Loading Troubleshooting

## Problem: Images Not Rendering

When using R2 storage, images might not load because:

### 1. R2 Bucket Public Access Not Enabled

Your R2 bucket needs public access enabled for images to load in the browser.

**Fix:**
1. Go to https://dash.cloudflare.com/
2. Navigate to **R2** → **wedding-photos** bucket
3. Click **Settings** tab
4. Under **Public Access**, click **Allow Access**
5. You'll get a public URL like: `https://pub-a82becfda869ee1e122e23fb03f77811.r2.dev`

### 2. CORS Not Configured

R2 needs CORS configured to allow browser access.

**Fix:**
1. In R2 bucket settings
2. Go to **CORS** section  
3. Add CORS policy:
```json
[
  {
    "AllowedOrigins": ["*"],
    "AllowedMethods": ["GET"],
    "AllowedHeaders": ["*"],
    "MaxAgeSeconds": 3600
  }
]
```

### 3. Check What URLs Are Being Generated

**Open Browser Console** (F12) and look for errors like:
- `403 Forbidden` → Public access not enabled
- `CORS error` → CORS not configured
- `404 Not Found` → Wrong URL format

**Expected URL format:**
```
https://pub-a82becfda869ee1e122e23fb03f77811.r2.dev/wedding-photos/event_2/abc123.webp
```

### 4. Verify R2 Configuration

Check your `.env` file:
```env
STORAGE_TYPE=r2
R2_ACCOUNT_ID=a82becfda869ee1e122e23fb03f77811
R2_ACCESS_KEY_ID=666c0bd9c7616b5fdd4a03bca126f2ab
R2_SECRET_ACCESS_KEY=782364f45ee6c0a48cf0c11fe03a0be9edf0c5f2f36580e9e294c721af505857
R2_BUCKET_NAME=wedding-photos
R2_PUBLIC_URL=  # Leave empty to use default
```

### 5. Test Upload & URL

1. Upload a photo via `/admin`
2. Check backend logs for the public URL
3. Copy that URL and paste in browser
4. Should load the image directly

Example log:
```
Image uploaded to R2: event_2/abc123.webp (45KB)
public_url: https://pub-xxx.r2.dev/wedding-photos/event_2/abc123.webp
```

### 6. Quick Fix: Enable Public Access Now

**Step-by-step:**
1. **Open** https://dash.cloudflare.com/
2. **Click** R2 in sidebar
3. **Click** on `wedding-photos` bucket
4. **Click** "Settings" tab
5. **Scroll** to "Public Access" section
6. **Click** "Allow Access" button
7. **Note** the public URL shown
8. **Done!** Images should now load

### 7. Alternative: Use Custom Domain (Advanced)

Instead of the default `pub-xxx.r2.dev` URL:

1. Add custom domain in R2 settings
2. Set up DNS CNAME record
3. Update `.env`:
```env
R2_PUBLIC_URL=https://photos.yourdomain.com
```

## Diagnostic Commands

### Check if image exists in R2:
```bash
curl -I "https://pub-a82becfda869ee1e122e23fb03f77811.r2.dev/wedding-photos/event_2/test.webp"
```

Expected: `200 OK` or `403 Forbidden` (not 404)

### Test from backend:
```python
# In backend directory
python -c "
from app.config import get_settings
s = get_settings()
print(f'Account: {s.R2_ACCOUNT_ID}')
print(f'Bucket: {s.R2_BUCKET_NAME}')
print(f'Public URL: https://pub-{s.R2_ACCOUNT_ID}.r2.dev/{s.R2_BUCKET_NAME}')
"
```

## Current Status

Based on your config, images should be at:
```
https://pub-a82becfda869ee1e122e23fb03f77811.r2.dev/wedding-photos/event_X/filename.webp
```

**Most likely issue:** Public access not enabled on the bucket.

**Solution:** Go enable public access in Cloudflare dashboard right now! Takes 30 seconds.

## Temporary Fix: Use Local Storage

If you need to test immediately while figuring out R2:

1. Edit `backend/.env`:
```env
STORAGE_TYPE=local
```

2. Restart backend
3. Upload photos → they go to local storage
4. Images will load immediately
5. Switch back to R2 when public access is enabled

## Need Help?

Check browser console for exact error messages!
Press F12 → Console tab → Look for red errors about images
