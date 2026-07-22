# 💒 AI Wedding Photo Portal

AI-powered wedding photo gallery with face recognition search. Photographers upload wedding photos, guests find themselves using a selfie.

## 🌟 Features

### For Photographers (`/admin`)
- 📤 **Batch Upload**: Multiple files or entire folders
- ⏱️ **Progress Tracking**: Real-time "Processing 5/50..."
- 🎯 **Auto Face Detection**: InsightFace powered
- 📊 **Upload Summary**: Success rate, face count, per-photo details

### For Guests (`/gallery`)
- 🖼️ **Pinterest-Style Grid**: Responsive masonry layout
- 🔍 **Selfie Search**: Find all photos containing your face
- 🎚️ **Smart Matching**: Adjustable similarity threshold
- 🔦 **Lightbox Viewer**: Click to view full size
- ✨ **Filtered View**: Show only search results

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- Node.js 18+
- PostgreSQL with pgvector extension
- Git

### Installation

```bash
# Clone repository
git clone <your-repo>
cd digital-album

# Backend setup
cd backend
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
pip install filetype opencv-python

# Create .env file
cp .env.example .env
# Edit .env with your database credentials

# Run migrations
alembic upgrade head

# Create test event
python create_test_event.py

# Start backend
python -m uvicorn app.main:app --reload

# Frontend setup (new terminal)
cd frontend
npm install
npm run dev
```

### Access
- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs

## 📖 Usage

### 1. Upload Photos (Photographer)
1. Navigate to http://localhost:3000/admin
2. Enter Event ID (default: 1)
3. Select multiple photos or folder
4. Click "Upload & Detect Faces"
5. Watch progress and results

### 2. Find Yourself (Guest)
1. Navigate to http://localhost:3000/gallery
2. Browse all wedding photos
3. Upload your selfie
4. Adjust similarity (0.3 = more results, 0.9 = strict)
5. Click "Find Me"
6. View only photos with your face

## 🏗️ Architecture

### Tech Stack
- **Backend**: FastAPI (Python)
- **Database**: PostgreSQL + pgvector
- **AI**: InsightFace (SCRFD + ArcFace)
- **Frontend**: React + Vite
- **Storage**: Local filesystem or Cloudflare R2 (configurable via `STORAGE_TYPE`)

### Project Structure
```
digital-album/
├── backend/
│   ├── app/
│   │   ├── api/routes/      # API endpoints
│   │   ├── models/          # Database models
│   │   ├── services/        # Business logic
│   │   ├── repositories/    # Data access
│   │   └── middleware/      # Custom middleware
│   ├── alembic/             # Migrations
│   ├── storage/photos/      # Uploaded photos
│   └── requirements.txt
│
├── frontend/
│   ├── src/
│   │   ├── pages/           # AdminPage, GalleryPage
│   │   ├── App.jsx          # Router
│   │   └── main.jsx
│   ├── vite.config.js
│   └── package.json
│
├── SETUP.md                 # Detailed setup instructions
├── FEATURES.md              # Feature documentation
└── QUICKSTART.md            # Quick testing guide
```

## 🔧 Configuration

### Environment Variables (backend/.env)
```env
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/wedding_photos
STORAGE_PATH=./storage/photos
MAX_FILE_SIZE=10485760        # 10MB
MAX_DIMENSION=8000
RESIZE_THRESHOLD=2000
DEBUG=True
LOG_LEVEL=INFO
```

### API Endpoints
- `POST /api/photos/upload` - Upload photo with face detection
- `POST /api/photos/search` - Search by selfie
- `GET /api/photos/event/{id}` - Get all photos for event
- `GET /storage/{path}` - Serve photo files
- `GET /health` - Health check

## 📊 Database Schema

### Tables
- **events**: Wedding events
- **photos**: Uploaded photos with metadata
- **face_embeddings**: 512-dimensional vectors (pgvector)

### Relationships
```
Event (1) ─→ (N) Photos (1) ─→ (N) FaceEmbeddings
```

## 🎯 How Face Recognition Works

1. **Upload**: Photographer uploads wedding photos
2. **Detection**: SCRFD detects all faces in each photo
3. **Embedding**: ArcFace generates 512-dim vector per face
4. **Storage**: Vectors stored in PostgreSQL pgvector column
5. **Search**: Guest uploads selfie → same pipeline → 1 vector
6. **Matching**: Cosine similarity query finds similar faces
7. **Results**: Matching photos returned, sorted by similarity

## 🚀 Deployment (Future)

### Current: Local Development
- Local filesystem storage
- Synchronous processing
- No authentication

### Production Ready (TODO)
- [x] Cloudflare R2 for images
- [x] Background face processing (in-process FastAPI BackgroundTasks)
- [x] WebP compression
- [ ] Authentication (JWT)
- [ ] Rate limiting
- [ ] CDN integration
- [ ] Docker deployment
- [ ] Railway/Vercel hosting

## 📝 Development Status

### ✅ Implemented (MVP)
- [x] Multiple/folder upload
- [x] Face detection (InsightFace)
- [x] Face embeddings (pgvector)
- [x] Selfie-based search
- [x] Pinterest-style gallery
- [x] Admin/client separation
- [x] Progress tracking
- [x] Lightbox viewer

### 🔜 Coming Soon
- [ ] Background processing
- [ ] Image compression
- [ ] Cloud storage
- [ ] Event management UI
- [ ] Authentication
- [ ] Batch download
- [ ] Social sharing

## 🐛 Troubleshooting

See [SETUP.md](./SETUP.md) for detailed troubleshooting.

**Common Issues:**
- Backend crashes → Missing dependencies (pip install)
- "Event not found" → Run `python create_test_event.py`
- Photos not showing → Check backend running, storage folder exists

## 📚 Documentation

- [SETUP.md](./SETUP.md) - Detailed setup and troubleshooting
- [FEATURES.md](./FEATURES.md) - Feature overview and UI mockups
- [QUICKSTART.md](./QUICKSTART.md) - Quick testing guide
- [backend/README.md](./backend/README.md) - Backend documentation

## 🤝 Contributing

This is a private project for Shoot @ Sight Weddings.

## 📄 License

Proprietary - All rights reserved

## 👥 Team

- **Developer**: Mad Tech Solutions
- **Client**: Shoot @ Sight Weddings (Pavithra Arun Kumar)

---

**Built with ❤️ using FastAPI, React, and InsightFace**
