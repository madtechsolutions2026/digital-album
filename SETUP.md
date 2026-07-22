# Setup Guide

How to get the AI Wedding Photo Portal running from a clean checkout: backend (FastAPI + PostgreSQL/pgvector + InsightFace), frontend (React/Vite), and the database migrations that create the schema.

## Prerequisites

- **Python 3.11+**
- **Node.js 18+**
- **PostgreSQL 15+** with the [pgvector](https://github.com/pgvector/pgvector) extension available
- ~2GB free RAM and ~1GB free disk space (InsightFace's `buffalo_l` model downloads on first run)
- A Cloudflare R2 bucket, *if* you want cloud storage (optional — local filesystem storage works out of the box)

No Redis or Celery is required — background face processing runs in-process via FastAPI's `BackgroundTasks`.

## 1. Database

Create the database and enable pgvector:

```sql
CREATE DATABASE wedding_photos;
\c wedding_photos
CREATE EXTENSION IF NOT EXISTS vector;
```

Docker alternative (already has pgvector built in):

```bash
docker run -d \
  --name wedding-photos-db \
  -e POSTGRES_PASSWORD=password \
  -e POSTGRES_DB=wedding_photos \
  -p 5432:5432 \
  pgvector/pgvector:pg15
```

## 2. Backend

```bash
cd backend
python -m venv venv

# Activate the virtual environment
venv\Scripts\activate        # Windows
source venv/bin/activate     # macOS/Linux

pip install -r requirements.txt
```

### Configure environment variables

```bash
cp .env.example .env
```

Edit `.env` and set at minimum `DATABASE_URL` to match your database. If you want Cloudflare R2 storage instead of local disk, set `STORAGE_TYPE=r2` and fill in the `R2_*` values; otherwise leave `STORAGE_TYPE=local`.

### Run database migrations

The schema (events, photos, face_embeddings with a pgvector column) is managed by Alembic — this must be run before starting the server:

```bash
alembic upgrade head
```

This applies, in order:
- `001_create_events_table.py`
- `002_create_photos_table.py`
- `003_create_face_embeddings_with_pgvector.py` (creates the pgvector column + similarity index)

To check what's applied: `alembic current`. To roll back one step: `alembic downgrade -1`.

### Start the backend

```bash
python -m uvicorn app.main:app --reload
```

The first request that triggers face detection will download the InsightFace `buffalo_l` model automatically (needs internet access, ~600MB, one-time). The API is now at `http://localhost:8000` (docs at `/docs`).

## 3. Frontend

```bash
cd frontend
npm install
npm run dev
```

Frontend is at `http://localhost:3000`.

## 4. First-time usage

1. Open `http://localhost:3000/admin`.
2. Create an event (name + date — the date is required).
3. Upload photos. Face detection runs automatically in the background right after upload finishes; the progress panel shows both stages (uploading, then detecting faces).
4. Once processing completes, go to `http://localhost:3000/gallery`, select the event, and search by uploading a selfie.

## Troubleshooting

**`alembic upgrade head` fails / relation already exists** — the database already has some of these tables from a prior run; check `alembic current` vs `alembic history` to see what's actually applied before re-running.

**`CREATE EXTENSION vector` fails** — pgvector isn't installed on your Postgres server. Use the Docker image above, or install the extension package for your OS/Postgres version.

**Face detection never runs / photos aren't searchable** — check that the backend process is actually running and reachable; face processing is a background task inside that same process, so if it restarts mid-job (e.g. `--reload` triggered by a file change) the job is lost. Re-trigger it via the event's "Process Faces" action in Admin.

**Uploads are slow** — a single large batch is CPU-bound on image compression; see `SPEED_OPTIMIZATION.md` for the tuning that's already in place. Photos are compressed to WebP targeting ~200KB before storage.

**R2 uploads fail / photos don't load** — confirm the R2 bucket has public access enabled and `R2_PUBLIC_URL` (or `R2_ACCOUNT_ID`) is correct; see `R2_SETUP.md`.
