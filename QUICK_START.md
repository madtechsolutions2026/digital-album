# 🚀 Quick Start Guide - Redis + Celery Setup

Follow these steps to get your face processing system running with Redis + Celery.

---

## 📋 Prerequisites Checklist

- [ ] PostgreSQL running with database created
- [ ] Python virtual environment activated
- [ ] Node.js and npm installed
- [ ] Backend `.env` file configured

---

## ⚡ Quick Setup (5 Steps)

### Step 1: Install Redis on Windows

**Easiest option - Memurai (Redis for Windows):**

1. Download: https://www.memurai.com/get-memurai
2. Run the installer (Memurai-Developer-v3.x.x.msi)
3. Install with default settings
4. Memurai starts automatically as a Windows service ✅

**Verify Redis is running:**
```powershell
redis-cli ping
```
Should return: `PONG` ✅

If `redis-cli` is not found, use full path:
```powershell
& "C:\Program Files\Memurai\redis-cli.exe" ping
```

---

### Step 2: Install Python Dependencies

```powershell
cd backend
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

This installs:
- `redis==5.0.1`
- `celery==5.3.4`
- `flower==2.0.1`
- All other dependencies

**Verify installation:**
```powershell
pip list | Select-String -Pattern "redis|celery"
```

Should show:
```
celery         5.3.4
flower         2.0.1
redis          5.0.1
```

---

### Step 3: Start Backend Server

**Terminal 1 (Backend):**
```powershell
cd c:\Users\vijay\digital-album\backend
.\venv\Scripts\Activate.ps1
python -m uvicorn app.main:app --reload
```

**✅ Success indicators:**
```
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
INFO:     Started reloader process
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Application startup complete.
```

**Test:** Open http://localhost:8000/health in browser
- Should return: `{"success": true, "message": "Service is healthy"}`

---

### Step 4: Start Celery Worker

**Terminal 2 (Celery Worker) - NEW TERMINAL:**
```powershell
cd c:\Users\vijay\digital-album\backend
.\venv\Scripts\Activate.ps1
celery -A celery_worker worker --loglevel=info --pool=solo
```

**⚠️ IMPORTANT:** Use `--pool=solo` on Windows!

**✅ Success indicators:**
```
-------------- celery@DESKTOP-XXXXX v5.3.4 (emerald-rush)
--- ***** -----
-- ******* ---- Windows-10-10.0.xxxxx
- *** --- * ---
- ** ---------- [config]
- ** ---------- .> app:         wedding_photos
- ** ---------- .> transport:   redis://localhost:6379/0
- ** ---------- .> results:     redis://localhost:6379/0
- *** --- * --- .> concurrency: 1 (solo)

[tasks]
  . app.tasks.face_processing.process_faces_task

[2024-xx-xx xx:xx:xx,xxx: INFO/MainProcess] Connected to redis://localhost:6379/0
[2024-xx-xx xx:xx:xx,xxx: INFO/MainProcess] celery@DESKTOP-XXXXX ready.
```

**Key things to check:**
- ✅ Shows: `Connected to redis://localhost:6379/0`
- ✅ Shows: `app.tasks.face_processing.process_faces_task` in task list
- ✅ Shows: `celery@HOSTNAME ready.`

---

### Step 5: Start Frontend

**Terminal 3 (Frontend) - NEW TERMINAL:**
```powershell
cd c:\Users\vijay\digital-album\frontend
npm run dev
```

**✅ Success indicators:**
```
VITE v5.x.x  ready in xxx ms

➜  Local:   http://localhost:5173/
➜  Network: use --host to expose
```

**Test:** Open http://localhost:5173/admin in browser

---

## 🧪 Testing the Face Processing System

### Test 1: Upload Photos

1. Go to http://localhost:5173/admin
2. Create or select an event (e.g., "Test Wedding")
3. Upload 3-5 photos using the upload button
4. **Expected behavior:**
   - Upload progress shows
   - Alert: "✅ X photos uploaded successfully! 🔍 Now detecting faces..."
   - Console shows: "Job <job_id> status: processing"

### Test 2: Monitor Background Processing

**Watch Terminal 2 (Celery Worker):**

You should see logs like:
```
[2024-xx-xx xx:xx:xx,xxx: INFO/MainProcess] Task app.tasks.face_processing.process_faces_task[<job_id>] received
[2024-xx-xx xx:xx:xx,xxx: INFO/MainProcess] Starting background face processing for event X
[2024-xx-xx xx:xx:xx,xxx: INFO/MainProcess] Found X photos to process for event X
[2024-xx-xx xx:xx:xx,xxx: INFO/MainProcess] Processed photo X: found X faces
[2024-xx-xx xx:xx:xx,xxx: INFO/MainProcess] Task app.tasks.face_processing.process_faces_task[<job_id>] succeeded
```

### Test 3: Check Frontend Polling

**Browser Console (F12 → Console):**

You should see:
```
Job <job_id> status: processing {current: 1, total: 5, percent_complete: 20, ...}
Job <job_id> status: processing {current: 2, total: 5, percent_complete: 40, ...}
...
Job <job_id> status: success
```

### Test 4: Verify Completion

**After 2-3 minutes (depends on number of photos):**

1. Alert appears: "✅ Face Detection Complete!"
2. Shows statistics:
   - Photos processed: X
   - Total faces found: X
   - Photos with no faces: X
3. Gallery page refreshes automatically
4. Face search should now work!

### Test 5: Test Face Search

1. Go to http://localhost:5173/gallery
2. Select the event
3. Upload a selfie of someone in the photos
4. Click "Find My Photos"
5. Should show all photos with that person

---

## 🔍 Testing Your 7 Uploaded Photos

Since you already have 7 photos uploaded but no faces detected:

### Option A: Use Manual Button

1. Go to http://localhost:5173/admin
2. Select your event
3. Click "🔍 Process Faces (Batch)" button
4. Confirm the dialog
5. Watch Terminal 2 (Celery) for processing logs
6. Wait for completion alert

### Option B: Use API Directly

**Test endpoint:**
```powershell
# Replace 1 with your event_id
curl http://localhost:8000/api/events/1/process-faces -X POST
```

**Response:**
```json
{
  "success": true,
  "message": "Face processing job queued successfully",
  "data": {
    "job_id": "abc123...",
    "event_id": 1,
    "status": "queued",
    "status_url": "/api/jobs/abc123.../status"
  }
}
```

**Check status:**
```powershell
# Replace abc123... with your job_id
curl http://localhost:8000/api/jobs/abc123.../status
```

---

## ✅ Success Checklist

After completing all steps, verify:

- [ ] Redis is running: `redis-cli ping` → PONG
- [ ] Backend is running: http://localhost:8000/health → healthy
- [ ] Celery worker shows: "celery@HOSTNAME ready"
- [ ] Frontend loads: http://localhost:5173/admin
- [ ] Can upload photos
- [ ] Auto-trigger shows alert
- [ ] Terminal 2 shows processing logs
- [ ] Completion alert appears
- [ ] Photos searchable by face

---

## 🐛 Common Issues & Solutions

### Issue 1: "redis-cli not found"

**Solution:**
```powershell
# Use full path
& "C:\Program Files\Memurai\redis-cli.exe" ping
```

### Issue 2: Celery worker fails to start

**Check 1:** Redis is running
```powershell
redis-cli ping
```

**Check 2:** Virtual environment is activated
```powershell
# Should show (venv) in prompt
.\venv\Scripts\Activate.ps1
```

**Check 3:** Dependencies installed
```powershell
pip list | Select-String celery
```

### Issue 3: "Connection refused" error

**Cause:** Redis not running

**Solution:** 
1. Check if Memurai service is running in Windows Services
2. Or start Redis manually:
```powershell
redis-server
```

### Issue 4: Face processing stays "pending"

**Cause:** Celery worker not running

**Solution:** Start Terminal 2 with Celery worker (see Step 4)

### Issue 5: ImportError or ModuleNotFoundError

**Solution:** Reinstall dependencies
```powershell
cd backend
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### Issue 6: Photos uploaded but no processing starts

**Check 1:** Look at browser console (F12) for errors

**Check 2:** Manually trigger processing:
- Click "🔍 Process Faces (Batch)" button

**Check 3:** Check backend logs (Terminal 1) for errors

---

## 📊 Monitoring Tools

### Option 1: Terminal Logs (Simple)

- **Terminal 1:** Backend API requests
- **Terminal 2:** Celery task execution (MOST IMPORTANT)
- **Browser Console:** Frontend status polling

### Option 2: Flower Web UI (Advanced)

**Start Flower:**
```powershell
cd backend
.\venv\Scripts\Activate.ps1
celery -A celery_worker flower
```

**Open:** http://localhost:5555

**Features:**
- See active workers
- Monitor task progress
- View task history
- Check success/failure rates

---

## 🎯 Expected Timeline

For 7 photos:

1. **Upload:** ~30 seconds (with skip_face_detection=true)
2. **Job queuing:** Instant (<1 second)
3. **Face processing:** ~20-30 seconds (3-4 seconds per photo)
4. **Total:** Under 1 minute

For 50 photos:

1. **Upload:** ~2 minutes
2. **Job queuing:** Instant
3. **Face processing:** ~3 minutes
4. **Total:** ~5 minutes

For 500 photos:

1. **Upload:** ~15 minutes
2. **Job queuing:** Instant
3. **Face processing:** ~25 minutes
4. **Total:** ~40 minutes (vs 60+ minutes before!)

---

## 🎉 What You've Achieved

✅ **Non-blocking uploads** - Photos appear immediately  
✅ **Background processing** - Face detection runs async  
✅ **Progress tracking** - Real-time status updates  
✅ **Scalable** - Can add multiple workers  
✅ **Production-ready** - Industry-standard architecture  
✅ **Resilient** - Automatic retries on failure  

---

## 🚀 Next Steps

1. **Test with your 7 photos** - Use manual button to process them
2. **Test face search** - Upload selfie and find photos
3. **Test larger batches** - Upload 20-30 photos
4. **Monitor performance** - Watch Terminal 2 for processing time
5. **Consider production** - Use Redis Cloud or AWS ElastiCache

---

## 📞 Need Help?

If something doesn't work:

1. Check all 3 terminals for error messages
2. Verify Redis: `redis-cli ping`
3. Check backend health: http://localhost:8000/health
4. Look at browser console (F12)
5. Share the error message

**Most common issue:** Celery worker not running → Start Terminal 2!

---

## 💡 Pro Tips

1. **Keep Terminal 2 (Celery) visible** - You'll see real-time processing
2. **Use Flower** for better monitoring - http://localhost:5555
3. **Check browser console** for job status updates
4. **Process in batches** - Upload → Process → Upload more
5. **Test with small batches first** - Verify everything works

---

**Ready to test? Follow the steps above and let me know if you encounter any issues!** 🚀
