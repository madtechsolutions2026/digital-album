# DG Album: Technology Stack and Railway Setup

## What the application does

DG Album is a wedding photo gallery. Photographers upload event photos; guests access an event gallery and can search for photos containing them by submitting a selfie. The backend stores photo metadata and face embeddings, while image files live in local storage or Cloudflare R2.

## Technology stack

| Layer | Technology | Role |
|---|---|---|
| Frontend | React 18, Vite 5, React Router, Axios | Admin and guest gallery single-page application |
| UI | Tailwind CSS, Framer Motion, Lucide, React Dropzone | Styling, transitions, icons, and multi-file selection |
| API | Python 3.11+, FastAPI, Uvicorn | REST endpoints for events, uploads, galleries, jobs, and face search |
| Database | PostgreSQL, SQLAlchemy async, asyncpg, Alembic | Event/photo records and schema migrations |
| Vector search | pgvector | Stores and compares 512-dimensional face embeddings |
| Face recognition | InsightFace (SCRFD detection + ArcFace embeddings), ONNX Runtime, OpenCV | Detects faces and creates searchable embeddings |
| Image handling | Pillow and WebP compression | Validates, resizes, and compresses uploaded images |
| Object storage | Cloudflare R2 through boto3 (S3-compatible) | Durable photo storage and public image URLs |
| Hosting | Railway with Railpack | Builds and runs the frontend and backend services |

## Request and data flow

1. The browser sends event and photo requests to the FastAPI service.
2. FastAPI validates and compresses photos, writes the image to R2 (or local storage), and stores metadata in PostgreSQL.
3. Face processing produces embeddings and stores them in pgvector.
4. Guest selfie search compares its embedding with event embeddings and returns matching photo URLs.

The app uses FastAPI `BackgroundTasks` for deferred face processing. This runs inside the API process, so an API restart can interrupt an active job. Redis and Celery are not part of the current runtime.

## Railway service configuration

The repository has separate Railpack configuration for `backend` and `frontend`. Configure each Railway service's root directory to match its folder.

### Backend service variables

Set these on the backend service:

| Variable | Value |
|---|---|
| `DATABASE_URL` | Railway PostgreSQL `DATABASE_URL` reference; the app rewrites `postgresql://` to `postgresql+asyncpg://` |
| `STORAGE_TYPE` | `r2` for durable image storage |
| `R2_ACCOUNT_ID` | Cloudflare account ID |
| `R2_ACCESS_KEY_ID` | R2 access key |
| `R2_SECRET_ACCESS_KEY` | R2 secret key |
| `R2_BUCKET_NAME` | R2 bucket name |
| `R2_PUBLIC_URL` | Public R2 bucket URL or custom image domain |
| `CORS_ORIGINS` | Exact public frontend origin, e.g. `https://dg-album-production.up.railway.app` |
| `JWT_SECRET` | A strong random secret used to sign gallery session tokens |

Keep R2 credentials and `JWT_SECRET` only in Railway's backend variables. Do not commit them to the repository. Use Railway's PostgreSQL service with the pgvector extension available, then run `alembic upgrade head` as a pre-deploy command (or once against the production database) before serving traffic.

The backend Railpack start command binds Uvicorn to `0.0.0.0:$PORT`, as Railway requires.

### Frontend service variables

Set `VITE_API_URL` on the frontend service to the backend's public HTTPS origin, without a trailing slash. For Railway service `Backend`, a reference variable can use:

```text
https://${{Backend.RAILWAY_PUBLIC_DOMAIN}}
```

Replace `Backend` with the exact backend service name shown in the Railway project. `VITE_API_URL` is embedded into the JavaScript bundle during the frontend build, so redeploy the frontend after changing it. The frontend now uses `localhost:8000` only in local Vite development; it will not send production browser requests to a visitor's localhost.

The frontend's Railpack start command serves the built static files on Railway's `$PORT`.

## Deployment checks

1. Open `<backend-origin>/health`; its response should report `success: true` and `database: connected`.
2. Open the frontend domain and check that it loads without a blank page.
3. In the browser network panel, verify API requests target the backend origin and return successful responses.
4. Create a test event, upload a sample photo, and confirm its image URL loads from R2.
5. Run face processing for the event, then search with a sample selfie.

Railway's filesystem is ephemeral across deployments. Use R2 rather than local storage for production photo files. The first face-processing request may download the InsightFace model, so allow sufficient memory and startup/request time.
