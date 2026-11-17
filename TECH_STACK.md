# DG Album technology overview

## Product flow

The public homepage introduces DG Album and lets a guest unlock a private wedding gallery with an event code and password. The photographer studio manages events and uploads. The API stores event and photo records, writes image files to local storage or Cloudflare R2, and creates face embeddings for selfie search.

## Stack

| Layer | Technology | Responsibility |
|---|---|---|
| Web UI | React 18, Vite 5, React Router | Product homepage, gallery access, photographer workspace |
| UI libraries | Tailwind CSS, Framer Motion, Lucide, React Dropzone | Styling, animation, icons, and multi-file selection |
| API | Python 3.11, FastAPI, Uvicorn | Event management, image upload, gallery sessions, face search |
| Data layer | PostgreSQL, SQLAlchemy async, asyncpg, Alembic | Event and photo metadata, migrations |
| Vector search | pgvector | Stores and compares face embeddings |
| Recognition | InsightFace (`buffalo_s` by default), ONNX Runtime, OpenCV | Face detection and 512-dimensional embeddings |
| Images | Pillow, WebP compression | Validation, resize, and storage optimization |
| Storage | Local files or Cloudflare R2 through boto3 | Stores uploaded images |
| Hosting | Railway Docker deployment | Runs the combined frontend and API service; PostgreSQL is a separate service |

## Access boundaries

- `GET /` is public and serves the product homepage.
- Guests enter an event code and password. The API issues an event-scoped JWT; gallery APIs validate that token.
- The photographer studio at `/admin` uses a separate studio username/password. Event listing, uploads, processing jobs, and event changes require this studio session.
- Local photo files are checked against the active event token before being returned. `/health` remains public for Railway health checks.

## Railway deployment

Railway builds the root `Dockerfile`. It builds the React bundle, installs the Python API dependencies, runs Alembic migrations, and starts a single Uvicorn worker on Railway's `$PORT`.

Required service variables:

- `DATABASE_URL` for Railway PostgreSQL with pgvector enabled.
- `ADMIN_USERNAME` and `ADMIN_PASSWORD` for photographer access.
- `JWT_SECRET` for guest gallery tokens.
- `STORAGE_TYPE=r2` plus `R2_ACCOUNT_ID`, `R2_ACCESS_KEY_ID`, `R2_SECRET_ACCESS_KEY`, `R2_BUCKET_NAME`, and `R2_PUBLIC_URL` for object storage.

The app temporarily accepts the existing `DEMO_USERNAME` and `DEMO_PASSWORD` variables as a migration fallback for photographer access. Rename them to `ADMIN_USERNAME` and `ADMIN_PASSWORD` in Railway, then remove the legacy variables. Keep all passwords and signing keys in Railway variables; do not commit them.

Use a private R2 bucket with expiring signed image URLs before storing real client galleries. Public object URLs can be opened by anyone who obtains the link. Local storage requires a mounted Railway volume and is not a substitute for a production backup strategy.
