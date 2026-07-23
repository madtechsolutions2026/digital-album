# Setup Guide

Run these in order. Two terminals needed at the end (backend + frontend).

## Prerequisites

- Python 3.11+
- Node.js 18+
- PostgreSQL 15+ with the [pgvector](https://github.com/pgvector/pgvector) extension
- (Optional) Cloudflare R2 bucket — skip if using local storage

No Redis/Celery needed.

## 1. Database

```bash
psql -U postgres
```
```sql
CREATE DATABASE wedding_photos;
\c wedding_photos
CREATE EXTENSION IF NOT EXISTS vector;
\q
```

Or with Docker instead of a local Postgres install:

```bash
docker run -d --name wedding-photos-db \
  -e POSTGRES_PASSWORD=password \
  -e POSTGRES_DB=wedding_photos \
  -p 5432:5432 \
  pgvector/pgvector:pg15
```

## 2. Backend

```bash
cd backend
python -m venv venv
venv\Scripts\activate          # Windows
# source venv/bin/activate     # macOS/Linux

pip install -r requirements.txt

cp .env.example .env
# edit .env: set DATABASE_URL (and R2_* if using STORAGE_TYPE=r2)

alembic upgrade head
```

Start it:

```bash
python -m uvicorn app.main:app --reload
```

Backend running at `http://localhost:8000` (docs at `/docs`). First face-detection request auto-downloads the InsightFace model (~600MB, needs internet).

## 3. Frontend

Open a second terminal:

```bash
cd frontend
npm install
npm run dev
```

Frontend running at `http://localhost:3000`.

## 4. Try it

1. `http://localhost:3000/admin` → create an event (name + date required)
2. Upload photos — face detection runs automatically in the background after upload
3. `http://localhost:3000/gallery` → select the event → upload a selfie to search

## Troubleshooting

| Problem | Fix |
|---|---|
| `alembic upgrade head` fails, table exists | Check `alembic current` vs `alembic history` — schema may already partially exist |
| `CREATE EXTENSION vector` fails | pgvector isn't installed on your Postgres — use the Docker command above instead |
| Photos never become searchable | Backend restarted mid-job (e.g. `--reload` fired) and killed the background task — re-run "Process Faces" on the event in Admin |
| R2 uploads fail / images don't load | Check bucket public access + `R2_PUBLIC_URL` in `.env` — see `R2_SETUP.md` |
| Uploads feel slow on large folders | Expected to be CPU-bound on compression; see `SPEED_OPTIMIZATION.md` |
