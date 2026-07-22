# Redis + Celery Setup Instructions for Windows

## 📦 Step 1: Install Redis on Windows

### Option A: Using WSL (Recommended for Production)

1. **Install WSL (Windows Subsystem for Linux):**
```powershell
wsl --install
```

2. **Install Redis in WSL:**
```bash
sudo apt update
sudo apt install redis-server
```

3. **Start Redis:**
```bash
sudo service redis-server start
```

4. **Verify Redis is running:**
```bash
redis-cli ping
# Should return: PONG
```

### Option B: Using Memurai (Native Windows - Easier)

1. **Download Memurai (Redis-compatible for Windows):**
   - Visit: https://www.memurai.com/get-memurai
   - Download Memurai Developer Edition (FREE)
   - Install the .msi file

2. **Memurai starts automatically as a Windows service**

3. **Verify Redis is running:**
```powershell
# Open PowerShell and test connection
redis-cli ping
# Should return: PONG
```

### Option C: Using Docker (If you have Docker Desktop)

```powershell
docker run -d -p 6379:6379 --name redis redis:latest
```

---

## 🐍 Step 2: Install Python Dependencies

Open PowerShell in the `backend` directory:

```powershell
cd backend
.\venv\Scripts\Activate.ps1

# Install Redis and Celery packages
pip install redis==5.0.1 celery==5.3.4 flower==2.0.1

# Verify installation
pip list | Select-String -Pattern "redis|celery|flower"
```

---

## 🚀 Step 3: Start the Services (3 Terminals Required)

### Terminal 1: Start Redis (if not using Memurai service)

**If using WSL:**
```bash
sudo service redis-server start
```

**If using Docker:**
```powershell
docker start redis
```

**If using Memurai:**
- Already running as Windows service - no action needed!

---

### Terminal 2: Start FastAPI Backend

```powershell
cd backend
.\venv\Scripts\Activate.ps1
python -m uvicorn app.main:app --reload
```

**Backend should start on:** http://localhost:8000

---

### Terminal 3: Start Celery Worker

```powershell
cd backend
.\venv\Scripts\Activate.ps1

# IMPORTANT: Windows requires --pool=solo
celery -A celery_worker worker --loglevel=info --pool=solo
```

**You should see:**
```
-------------- celery@HOSTNAME v5.3.4 (emerald-rush)
--- ***** -----
-- ******* ---- Windows-10-10.0.xxxxx
- *** --- * ---
- ** ---------- [config]
- ** ---------- .> app:         wedding_photos:0x...
- ** ---------- .> transport:   redis://localhost:6379/0
- ** ---------- .> results:     redis://localhost:6379/0
- *** --- * --- .> concurrency: 1 (solo)
-- ******* ---- .> task events: ON
--- ***** -----
-------------- [queues]
                .> face_processing exchange=face_processing(direct) key=face_processing

[tasks]
  . app.tasks.face_processing.process_faces_task

[2024-xx-xx xx:xx:xx,xxx: INFO/MainProcess] Connected to redis://localhost:6379/0
[2024-xx-xx xx:xx:xx,xxx: INFO/MainProcess] mingle: searching for neighbors
[2024-xx-xx xx:xx:xx,xxx: INFO/MainProcess] mingle: all alone
[2024-xx-xx xx:xx:xx,xxx: INFO/MainProcess] celery@HOSTNAME ready.
```

---

### Terminal 4: Start Frontend (Optional - if needed)

```powershell
cd frontend
npm run dev
```

**Frontend should start on:** http://localhost:5173

---

## ✅ Step 4: Verify Everything Works

### Test 1: Check Redis Connection

```powershell
redis-cli ping
# Should return: PONG
```

### Test 2: Check Backend Health

Open browser: http://localhost:8000/health

Should return:
```json
{
  "success": true,
  "message": "Service is healthy",
  "data": {
    "status": "healthy",
    "database": "connected",
    "version": "1.0.0"
  }
}
```

### Test 3: Check Celery Worker

Look at Terminal 3 (Celery worker) - should show:
```
[INFO/MainProcess] celery@HOSTNAME ready.
```

### Test 4: Test Face Processing

1. Go to http://localhost:5173/admin
2. Create or select an event
3. Upload 2-3 photos
4. Wait for auto-trigger or click "Process Faces" button
5. Watch Terminal 3 (Celery) for processing logs
6. Frontend should show progress notifications

---

## 🐛 Troubleshooting

### Issue: "redis-cli not found"

**Solution:** Add Redis to PATH or use full path:
```powershell
# For Memurai
C:\Program Files\Memurai\redis-cli.exe ping
```

### Issue: Celery worker fails with "ImportError"

**Solution:** Make sure you're in the backend directory and venv is activated:
```powershell
cd backend
.\venv\Scripts\Activate.ps1
celery -A celery_worker worker --loglevel=info --pool=solo
```

### Issue: "Connection refused" when starting Celery

**Solution:** Redis is not running. Start Redis first (see Step 1).

### Issue: Celery worker crashes on Windows

**Solution:** Use `--pool=solo` flag (required for Windows):
```powershell
celery -A celery_worker worker --loglevel=info --pool=solo
```

### Issue: Face processing job stays in "pending" state

**Possible causes:**
1. Celery worker not running → Start Terminal 3
2. Redis not running → Check `redis-cli ping`
3. Task not registered → Check Terminal 3 logs for task list

### Issue: Backend fails to start - "No module named 'celery'"

**Solution:** Install dependencies:
```powershell
cd backend
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

---

## 📊 Optional: Monitor Celery with Flower

Flower provides a web UI to monitor Celery tasks.

### Start Flower (Terminal 5):

```powershell
cd backend
.\venv\Scripts\Activate.ps1
celery -A celery_worker flower
```

**Open:** http://localhost:5555

You can see:
- Active workers
- Task history
- Success/failure rates
- Real-time progress

---

## 🎯 Complete Startup Checklist

- [ ] Redis server is running (`redis-cli ping` returns PONG)
- [ ] Backend dependencies installed (`pip list | grep celery`)
- [ ] Backend server running (Terminal 2)
- [ ] Celery worker running (Terminal 3)
- [ ] Frontend running (Terminal 4) - optional
- [ ] Can access http://localhost:8000/health
- [ ] Can access http://localhost:5173/admin

---

## 🔄 Daily Workflow

**Every time you start working:**

```powershell
# Terminal 1: Start Redis (if not using Memurai service)
# Skip if Memurai is running as service

# Terminal 2: Backend
cd backend
.\venv\Scripts\Activate.ps1
python -m uvicorn app.main:app --reload

# Terminal 3: Celery Worker
cd backend
.\venv\Scripts\Activate.ps1
celery -A celery_worker worker --loglevel=info --pool=solo

# Terminal 4: Frontend (optional)
cd frontend
npm run dev
```

---

## 🎉 Success Indicators

When everything is working:

1. **Redis:** `redis-cli ping` → PONG
2. **Backend:** http://localhost:8000/health → status: healthy
3. **Celery:** Terminal shows "celery@HOSTNAME ready"
4. **Upload photos:** Photos appear in gallery immediately
5. **Face processing:** 
   - Console shows "Job <id> status: processing"
   - After 2-3 minutes: "Face Detection Complete!"
   - Photos searchable by face

---

## 📝 Environment Variables

Add to `backend/.env` (optional - defaults work fine):

```env
# Redis Configuration (optional - defaults to localhost)
REDIS_URL=redis://localhost:6379/0
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0
```

---

## 🚀 Production Deployment

For production, consider:

1. **Redis Cloud:** Free tier at https://redis.com/try-free/
2. **Heroku Redis:** $15/month addon
3. **AWS ElastiCache:** Managed Redis service
4. **Supervisor:** Auto-restart Celery workers
5. **Flower with auth:** Monitor jobs securely

---

## 📞 Need Help?

Check logs:
- **Backend:** Terminal 2
- **Celery:** Terminal 3 (most important for face processing)
- **Browser console:** F12 → Console tab
- **Redis:** `redis-cli MONITOR` (shows all Redis commands)

---

## 🎓 Summary

You now have a professional background job processing system:

✅ **Fast uploads** - Photos in gallery immediately  
✅ **Background processing** - Face detection runs async  
✅ **Progress tracking** - Frontend polls job status  
✅ **Scalable** - Add more Celery workers anytime  
✅ **Resilient** - Jobs retry on failure  
✅ **Production-ready** - Redis handles thousands of jobs  

**Next steps:** Test with your 7 photos and verify face search works!
