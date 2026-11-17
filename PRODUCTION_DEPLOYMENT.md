# DG Album Production Deployment

The public homepage and guest gallery are open. Wedding galleries stay private behind each event's access code and password. Photographer event management is protected at `/admin` by a studio username and password.

## Railway configuration

Keep the existing Railway PostgreSQL service and its pgvector extension. The container runs `alembic upgrade head` before Uvicorn starts.

Set these service variables:

| Variable | Purpose |
|---|---|
| `DATABASE_URL` | Railway PostgreSQL connection string |
| `ADMIN_USERNAME` | Photographer studio sign-in name |
| `ADMIN_PASSWORD` | Strong studio sign-in password |
| `JWT_SECRET` | Strong secret for event-scoped guest session tokens |
| `STORAGE_TYPE` | `local` with the Railway photo volume mounted at `STORAGE_PATH` |

The application temporarily accepts existing `DEMO_USERNAME` and `DEMO_PASSWORD` values as fallback studio credentials, so removing the public demo gate does not lock the photographer out. Move those values to `ADMIN_USERNAME` and `ADMIN_PASSWORD` in Railway, then remove the legacy variables. Keep credentials and signing secrets in Railway variables; never commit them.

## Public flows

- `/` shows the product website and event-code entry form.
- `/gallery` opens the event access flow. Each event code/password issues a token scoped to that event.
- `/admin` redirects to the photographer studio sign-in. Event listing, uploads, processing jobs, and event changes require the studio session.
- `/health` remains public for Railway's deployment health check.

Local stored photos are only served when their database record belongs to the active gallery session. Mount the Railway photo volume at the configured `STORAGE_PATH`. R2 uploads currently return direct object URLs, so use the local volume for private galleries until signed R2 URLs are implemented; anyone with a public R2 image link can open it.

## Deploy and verify

Build the Dockerfile in the project root and deploy to the Railway `dg-album` service. After the service is healthy:

1. Visit the public domain and confirm the landing page loads without a demo sign-in.
2. Visit `/admin`; confirm it asks for studio credentials and opens the photographer workspace after sign-in.
3. Create a test event and keep its generated guest access code and password.
4. Upload a non-client test image, unlock that event from the public gallery, and confirm its image loads.
5. Check `/health` reports a connected database.

Avoid deleting existing events or photos as part of a deployment check.
