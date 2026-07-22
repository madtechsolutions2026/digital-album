# Wedding Photo Portal - Quick Start Guide

## ✅ What's Running

Your application is now running with:

- **Backend API**: http://localhost:8000
- **Frontend React App**: http://localhost:3000

## 🚀 Access the Application

Open your browser and go to: **http://localhost:3000**

## 📸 Test Face Detection

### Step 1: Upload Wedding Photos (Multiple Files or Folder)
1. Click on the "Upload Photos" tab
2. Event ID should be `1` (default)
3. Click "Select Photos" and either:
   - **Select multiple files**: Hold Ctrl/Cmd and select 5-50 images
   - **Select entire folder**: Choose a folder containing wedding photos
4. You'll see a file count (e.g., "25 files selected")
5. Click "Upload & Detect Faces"
6. Watch the progress: "Processing photo 5/25..."
7. View results showing:
   - How many photos succeeded/failed
   - Total faces detected across all photos
   - Per-photo details: Photo ID, face count, embeddings stored

### Step 2: Search for Your Face
1. Click on the "Search by Face" tab
2. Event ID should be `1` (same as upload)
3. Upload a clear selfie of yourself
4. Adjust the threshold slider (start with 0.6)
5. Click "Find My Photos"
6. View matching photos with similarity scores

## 🛠️ If You Need to Restart

### Backend (Terminal 1):
```bash
cd backend
python -m uvicorn app.main:app --reload
```

### Frontend (Terminal 2):
```bash
cd frontend
npm run dev
```

## 📊 Check API Health

Visit: http://localhost:8000/health

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

## 🎯 Features

### Upload Tab
- Automatic face detection using InsightFace
- Preview uploaded image before submission
- Shows number of faces detected
- Stores face embeddings for search

### Search Tab  
- Upload your selfie to find photos of yourself
- Adjustable similarity threshold (0.3 - 0.9)
- Returns matching photos with:
  - Photo ID
  - Similarity score (percentage)
  - Face bounding box coordinates

## 🐛 Troubleshooting

### Backend Issues
- Check database is running: `psql -U postgres -d wedding_photos`
- Check logs in the terminal running uvicorn
- Health check: http://localhost:8000/health

### Frontend Issues
- Check browser console for errors (F12)
- Verify backend is running on port 8000
- Clear browser cache and reload

### No Faces Detected
- Ensure the photo has clear, visible faces
- Photo should be JPEG, PNG, or WEBP
- Face should be reasonably large in the frame
- Good lighting helps detection accuracy

### No Search Results
- Lower the threshold (try 0.4 or 0.5)
- Ensure you uploaded photos first
- Verify same Event ID for upload and search
- Use a clear frontal selfie for best results

## 📝 API Documentation

Interactive docs: http://localhost:8000/docs

## 💾 Database

- Name: `wedding_photos`
- Host: `localhost:5432`
- User: `postgres`

## 🎨 Project Structure

```
digital-album/
├── backend/              # FastAPI backend
│   ├── app/
│   │   ├── api/         # API routes
│   │   ├── models/      # Database models
│   │   ├── services/    # Business logic
│   │   └── repositories/# Data access
│   └── alembic/         # Database migrations
│
└── frontend/            # React frontend
    ├── src/
    │   ├── App.jsx      # Main component
    │   └── App.css      # Styling
    └── vite.config.js   # Vite configuration
```

## 🎉 Enjoy!

Your AI-powered wedding photo portal is ready to use!
