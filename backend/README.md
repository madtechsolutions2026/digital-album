# AI-Powered Wedding Photo Portal - Backend

FastAPI-based backend system that enables automatic face recognition and photo matching at wedding events using InsightFace and PostgreSQL with pgvector.

## Features

- **Photo Upload with Face Detection**: Automatically detect and extract facial features from uploaded photos
- **Face-Based Search**: Find all photos containing a specific person using a selfie
- **Vector Similarity Search**: Efficient face matching using PostgreSQL pgvector extension
- **RESTful API**: Clean, documented API endpoints with automatic OpenAPI docs

## Technology Stack

- **FastAPI 0.115+**: Modern async web framework
- **PostgreSQL 15+**: Relational database with pgvector extension
- **InsightFace**: Face detection and embedding generation (buffalo_l model)
- **SQLAlchemy 2.0+**: Async ORM
- **Alembic**: Database migrations
- **Pillow 10+**: Image processing

## Prerequisites

- Python 3.11+
- PostgreSQL 15+ with pgvector extension
- 2GB+ RAM (for InsightFace model)

## Setup Instructions

### 1. Install PostgreSQL with pgvector

**Ubuntu/Debian:**
```bash
sudo apt-get update
sudo apt-get install postgresql-15 postgresql-15-pgvector
```

**macOS (using Homebrew):**
```bash
brew install postgresql@15 pgvector
brew services start postgresql@15
```

**Docker:**
```bash
docker run -d \
  --name wedding-photos-db \
  -e POSTGRES_PASSWORD=password \
  -e POSTGRES_DB=wedding_photos \
  -p 5432:5432 \
  pgvector/pgvector:pg15
```

### 2. Create Database

```bash
# Connect to PostgreSQL
psql -U postgres

# Create database
CREATE DATABASE wedding_photos;

# Connect to the database
\c wedding_photos

# Enable pgvector extension
CREATE EXTENSION vector;

# Exit psql
\q
```

### 3. Set Up Python Environment

```bash
# Navigate to backend directory
cd backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Linux/macOS:
source venv/bin/activate
# On Windows:
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install development dependencies (optional)
pip install -r requirements-dev.txt
```

### 4. Configure Environment Variables

```bash
# Copy example environment file
cp .env.example .env

# Edit .env file with your configuration
# Required variables:
# - DATABASE_URL: PostgreSQL connection string
# - STORAGE_PATH: Directory for storing uploaded photos
# - CORS_ORIGINS: Allowed frontend origins
```

**Example .env configuration:**
```env
DATABASE_URL=postgresql+asyncpg://postgres:password@localhost:5432/wedding_photos
STORAGE_PATH=/app/storage/photos
DEBUG=false
LOG_LEVEL=INFO
CORS_ORIGINS=http://localhost:3000
```

### 5. Create Storage Directory

```bash
# Create directory for photo storage
mkdir -p /app/storage/photos

# Or use a relative path
mkdir -p ./storage/photos
# Update STORAGE_PATH in .env to ./storage/photos
```

### 6. Run Database Migrations

```bash
# Initialize Alembic (first time only)
alembic init alembic

# Generate initial migration
alembic revision --autogenerate -m "Initial schema with events, photos, and face_embeddings"

# Apply migrations
alembic upgrade head
```

### 7. Download InsightFace Model

The buffalo_l model will be automatically downloaded on first run. Ensure you have internet connectivity and approximately 600MB of free disk space.

## Running the Server

### Development Mode

```bash
# With auto-reload enabled
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Production Mode

```bash
# Using uvicorn with multiple workers
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

### Using Gunicorn (Production)

```bash
# Install gunicorn
pip install gunicorn

# Run with uvicorn workers
gunicorn app.main:app \
  --workers 4 \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8000 \
  --access-logfile - \
  --error-logfile -
```

## API Documentation

Once the server is running, access the interactive API documentation:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI JSON**: http://localhost:8000/openapi.json

## API Endpoints

### Photo Upload
```http
POST /api/photos/upload
Content-Type: multipart/form-data

Parameters:
- file: image file (JPEG, PNG, or WEBP)
- event_id: integer (event ID)

Response:
{
  "success": true,
  "message": "Photo uploaded with 3 faces detected",
  "data": {
    "photo_id": 123,
    "face_count": 3,
    "file_path": "event_1/uuid.jpg"
  }
}
```

### Face Search
```http
POST /api/photos/search
Content-Type: multipart/form-data

Parameters:
- selfie: image file (JPEG, PNG, or WEBP)
- event_id: integer (event ID)
- threshold: float (optional, default: 0.6)

Response:
{
  "success": true,
  "message": "Found 15 matching photos",
  "data": {
    "matches": [
      {
        "photo_id": 123,
        "file_path": "event_1/uuid.jpg",
        "similarity_score": 0.92,
        "bounding_box": {"x1": 100, "y1": 150, "x2": 300, "y2": 400}
      }
    ],
    "query_face_confidence": 0.98
  }
}
```

## Database Migrations

### Create a New Migration

```bash
# After modifying SQLAlchemy models
alembic revision --autogenerate -m "Description of changes"
```

### Apply Migrations

```bash
# Apply all pending migrations
alembic upgrade head

# Upgrade to specific revision
alembic upgrade <revision_id>

# Rollback one migration
alembic downgrade -1

# Rollback to specific revision
alembic downgrade <revision_id>
```

### View Migration History

```bash
# Show current migration version
alembic current

# Show migration history
alembic history

# Show pending migrations
alembic history --verbose
```

## Testing

### Run All Tests

```bash
# Run all tests with coverage
pytest --cov=app --cov-report=html

# Run only property-based tests
pytest tests/property_tests/

# Run only integration tests
pytest tests/integration_tests/

# Run with verbose output
pytest -v
```

### Run Specific Test File

```bash
pytest tests/property_tests/test_image_validation.py -v
```

### Run Tests with Hypothesis Profile

```bash
# Use CI profile (100 iterations)
pytest tests/property_tests/ --hypothesis-profile=ci

# Use dev profile (20 iterations)
pytest tests/property_tests/ --hypothesis-profile=dev
```

## Project Structure

```
backend/
├── app/
│   ├── api/
│   │   └── routes/          # API endpoint definitions
│   ├── models/              # SQLAlchemy ORM models
│   ├── services/            # Business logic layer
│   ├── repositories/        # Data access layer
│   ├── middleware/          # Custom middleware
│   ├── database.py          # Database session management
│   ├── config.py            # Configuration settings
│   ├── exceptions.py        # Custom exceptions
│   └── main.py              # FastAPI application entry point
├── alembic/                 # Database migrations
├── tests/
│   ├── property_tests/      # Property-based tests
│   ├── integration_tests/   # Integration tests
│   └── unit_tests/          # Unit tests
├── storage/                 # Photo storage (created at runtime)
├── requirements.txt         # Production dependencies
├── requirements-dev.txt     # Development dependencies
├── .env                     # Environment variables (not in git)
├── .env.example             # Example environment file
└── README.md                # This file
```

## Configuration

All configuration is managed through environment variables. See `.env.example` for available options.

### Key Configuration Options

- **DATABASE_URL**: PostgreSQL connection string with asyncpg driver
- **STORAGE_PATH**: Absolute or relative path for photo storage
- **DEBUG**: Enable debug mode (true/false)
- **LOG_LEVEL**: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
- **CORS_ORIGINS**: Comma-separated list of allowed origins
- **MAX_FILE_SIZE_MB**: Maximum upload file size (default: 10)
- **DEFAULT_SIMILARITY_THRESHOLD**: Default face matching threshold (default: 0.6)

## Troubleshooting

### Database Connection Issues

```bash
# Test PostgreSQL connection
psql -U postgres -d wedding_photos -c "SELECT version();"

# Check if pgvector extension is installed
psql -U postgres -d wedding_photos -c "SELECT * FROM pg_extension WHERE extname = 'vector';"
```

### InsightFace Model Download Issues

If the model fails to download automatically:
```bash
# Manually download and place in ~/.insightface/models/buffalo_l/
mkdir -p ~/.insightface/models/buffalo_l
# Download from InsightFace repository
```

### Storage Permission Issues

```bash
# Ensure storage directory has write permissions
chmod -R 755 /app/storage/photos

# Or use a directory in your user home
mkdir -p ~/wedding-photos-storage
# Update STORAGE_PATH in .env
```

### Port Already in Use

```bash
# Check what's using port 8000
lsof -i :8000  # macOS/Linux
netstat -ano | findstr :8000  # Windows

# Run on different port
uvicorn app.main:app --port 8001
```

## Performance Considerations

- **Connection Pooling**: Configured for 20 base connections + 40 overflow
- **pgvector HNSW Index**: Provides sub-20ms p95 query latency
- **Image Resizing**: Images >2048px are resized before face detection
- **Async Processing**: All I/O operations use async/await for concurrency

## Security Notes

- File uploads are validated by header inspection, not just extensions
- Filenames are sanitized to prevent directory traversal
- File size and dimension limits prevent resource exhaustion
- Database uses connection pooling with timeouts
- Error responses don't expose internal system details

## License

This project is proprietary and confidential.

## Support

For issues or questions, please contact the development team.
