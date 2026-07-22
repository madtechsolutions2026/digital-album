# Wedding Photo Portal - Features Overview

## 🎯 Two Separate Interfaces

### 1. `/admin` - Photographer Interface
**Purpose**: Upload and manage wedding photos

**Features**:
- 📤 Multiple file upload (select 5, 10, 50+ photos)
- 📁 Folder upload (select entire wedding folder)
- ⏱️ Real-time progress ("Processing photo 5/50...")
- 🎯 Automatic face detection on all photos
- 📊 Upload summary statistics
- ✅ Per-photo results showing:
  - Photo ID
  - Number of faces detected
  - Embeddings stored
  - Success/failure status

### 2. `/gallery` - Client/Guest Interface
**Purpose**: View photos and find yourself

**Features**:
- 🖼️ **Pinterest-style photo grid** - Responsive masonry layout
- 🔍 **Selfie search** - Upload your photo to find yourself
- 🎚️ **Adjustable similarity threshold** (0.3 - 0.9)
- 🔦 **Lightbox view** - Click any photo to view full size
- ✨ **Search highlighting** - Shows only matching photos
- 📱 **Responsive design** - Works on mobile and desktop

## 🚀 User Flows

### Photographer Workflow
1. Go to `/admin`
2. Select Event ID (e.g., 1)
3. Upload wedding photos (multiple files or folder)
4. Watch progress bar
5. Review results:
   - 45 successful uploads
   - 0 failures
   - 127 total faces detected

### Guest Workflow
1. Go to `/gallery` (or `/`)
2. Browse all wedding photos in Pinterest-style grid
3. Upload a selfie to search
4. Adjust similarity threshold if needed
5. Click "Find Me"
6. View only photos containing their face
7. Click any photo to view full size
8. Clear search to see all photos again

## 🎨 UI Highlights

### Gallery Page
```
┌─────────────────────────────────────────┐
│  🔍 Find Your Photos                    │
│  Upload a selfie to find photos         │
│  containing your face                   │
│                                         │
│  [📤 Upload Selfie] [Similarity: 0.60] │
│  [🔍 Find Me] [❌ Clear Search]         │
├─────────────────────────────────────────┤
│                                         │
│  ┌───┐ ┌────┐ ┌──┐  ┌────┐            │
│  │   │ │    │ │  │  │    │            │
│  │img│ │ img│ │im│  │img │  ← Masonry │
│  │   │ │    │ │g │  │    │    Grid    │
│  └───┘ └────┘ └──┘  └────┘            │
│  ┌──┐ ┌───┐  ┌────┐ ┌──┐             │
│  │  │ │   │  │    │ │  │             │
│  │im│ │img│  │img │ │im│             │
│  │g │ │   │  │    │ │g │             │
│  └──┘ └───┘  └────┘ └──┘             │
│                                         │
└─────────────────────────────────────────┘
```

### Admin Page
```
┌─────────────────────────────────────────┐
│  Upload Wedding Photos                  │
│  Upload multiple photos or an entire    │
│  folder with face detection             │
│                                         │
│  Event ID: [1]                          │
│  [Select Files/Folder]                  │
│                                         │
│  25 files selected                      │
│  📷 IMG_001.jpg                         │
│  📷 IMG_002.jpg                         │
│  ... and 23 more files                  │
│                                         │
│  [🎯 Upload & Detect Faces]            │
│                                         │
│  ⏳ Processing photo 8/25...           │
│  [████████░░░░░░░░] 32%                │
└─────────────────────────────────────────┘
```

## 🔧 Technical Implementation

### Frontend Routes
- `/` → Gallery (default)
- `/gallery` → Gallery view
- `/admin` → Admin upload interface

### Backend Endpoints
- `POST /api/photos/upload` - Upload photo with face detection
- `POST /api/photos/search` - Search by selfie
- `GET /api/photos/event/{id}` - Get all photos for event
- `GET /storage/{path}` - Serve photo files
- `GET /health` - Health check

### Data Flow
```
Admin Upload:
File → Validate → Detect Faces → Extract Embeddings → Store

Client Search:
Selfie → Detect Face → Extract Embedding → 
Similarity Query → Matching Photos
```

## 🎯 Key Features Status

✅ **Implemented**:
- Multiple/folder file upload
- Real-time progress tracking
- Face detection (InsightFace)
- Face embeddings storage (pgvector)
- Pinterest-style photo grid
- Selfie-based search
- Adjustable similarity threshold
- Lightbox image viewer
- Separate admin/client interfaces

🔜 **Future** (not implemented yet):
- Background job processing (Redis/Celery)
- Image compression (WebP)
- Cloudflare R2 storage
- Event management UI
- User authentication
- Photo categories/tags
- Download all photos feature
- Social sharing

## 🚀 Quick Start

1. Start backend: `cd backend && python -m uvicorn app.main:app --reload`
2. Start frontend: `cd frontend && npm run dev`
3. Open **http://localhost:3000**
4. Try `/admin` to upload photos
5. Try `/gallery` to view and search

## 📝 Notes

- Photos are currently stored in `backend/storage/photos/event_{id}/`
- No authentication - add before production
- Processing is synchronous (no background jobs yet)
- Event 1 must exist before uploading (run `create_test_event.py`)
