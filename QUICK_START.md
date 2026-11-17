# Digital Album Quick Start (Windows)

This project uses a FastAPI backend, PostgreSQL with pgvector, and a Vite frontend. Face processing runs in the backend; Redis and Celery are not required.

## Prerequisites

- Python 3.11+
- Node.js 18+ (includes npm)
- PostgreSQL 15+ with the pgvector extension

## 1. Prepare the database

Create a database named `wedding_photos` and enable pgvector:

```sql
CREATE DATABASE wedding_photos;
\c wedding_photos
CREATE EXTENSION IF NOT EXISTS vector;
```

Alternatively, start a local database with Docker:

```powershell
docker run -d --name wedding-photos-db -e POSTGRES_PASSWORD=password -e POSTGRES_DB=wedding_photos -p 5432:5432 pgvector/pgvector:pg15
```

## 2. Configure and start the backend

In PowerShell, from the project root:

```powershell
cd backend
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item .env.example .env
```

Edit `backend\.env` and set `DATABASE_URL` to match your PostgreSQL credentials. For the Docker command above, use:

```env
DATABASE_URL=postgresql+asyncpg://postgres:password@localhost:5432/wedding_photos
STORAGE_TYPE=local
STORAGE_PATH=./storage/photos
```

Then run migrations and start the API:

```powershell
alembic upgrade head
python -m uvicorn app.main:app --reload
```

Keep this terminal open. Confirm the API responds at <http://localhost:8000/health>.

## 3. Start the frontend

Open a second PowerShell terminal:

```powershell
cd frontend
npm install
npm run dev
```

Open <http://localhost:3000/admin> to create an event and upload photos. Open <http://localhost:3000/gallery> to access an event gallery. Face detection is lazy-loaded on the first processing request and may download the InsightFace model (about 600 MB).

## If startup fails

- **Database connection refused:** Start PostgreSQL and verify the host, port, username, password, and database in `backend\.env`.
- **`alembic upgrade head` fails with a missing vector type:** Install pgvector for your PostgreSQL version, then run `CREATE EXTENSION IF NOT EXISTS vector;` in `wedding_photos`.
- **Frontend says `vite` is not recognized:** Run `npm install` from `frontend`, then retry `npm run dev`.
- **Photos do not load from R2:** Set `STORAGE_TYPE=r2` and configure the `R2_*` values in `backend\.env`; see `R2_SETUP.md`.
- **Photos uploaded with detection skipped are not searchable:** Use Admin's Process Faces action for that event.
