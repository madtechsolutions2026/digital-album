"""Apply database migrations and start the DG Album web application."""
import os
import subprocess
import sys

if not (os.environ.get("ADMIN_PASSWORD") or os.environ.get("DEMO_PASSWORD")):
    raise RuntimeError("Set ADMIN_PASSWORD to enable protected photographer access.")

subprocess.run([sys.executable, "-m", "alembic", "upgrade", "head"], check=True)
os.execv(
    sys.executable,
    [
        sys.executable,
        "-m",
        "uvicorn",
        "app.main:app",
        "--host",
        "0.0.0.0",
        "--port",
        os.environ.get("PORT", "8080"),
        "--workers",
        "1",
        "--proxy-headers",
    ],
)
