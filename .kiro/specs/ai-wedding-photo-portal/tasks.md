# Implementation Plan: AI-Powered Wedding Photo Portal Backend

## Overview

This implementation plan breaks down the FastAPI-based wedding photo portal backend into discrete coding tasks. The system uses InsightFace for face detection, PostgreSQL with pgvector for vector similarity search, and provides REST API endpoints for photo upload and face-based search. Each task builds incrementally, validating functionality through code and tests.

## Tasks

- [ ] 1. Set up project structure and dependencies
  - Create `backend/` directory with FastAPI project structure
  - Create subdirectories: `app/`, `app/api/`, `app/api/routes/`, `app/models/`, `app/services/`, `app/repositories/`, `app/middleware/`, `alembic/`, `tests/`
  - Create `requirements.txt` with pinned versions: FastAPI 0.115+, SQLAlchemy 2.0+, asyncpg, psycopg2-binary, pgvector, insightface, onnxruntime, Pillow 10+, alembic 1.13+, pydantic-settings, python-multipart, python-dotenv, filetype
  - Create `requirements-dev.txt` with pytest, pytest-asyncio, pytest-cov, hypothesis 6.100+, httpx, python-json-logger
  - Create `.env.example` file with all required environment variables (DATABASE_URL, STORAGE_PATH, DEBUG, LOG_LEVEL, CORS_ORIGINS)
  - Create `README.md` with setup instructions, environment setup, database migration commands, and how to run the server
  - _Requirements: 1.1, 1.3, 1.4_

- [ ] 2. Implement database configuration and session management
  - [ ] 2.1 Create database configuration with SQLAlchemy async engine
    - Implement `backend/app/database.py` with `create_async_engine` configured with pool settings (pool_size=20, max_overflow=40, pool_recycle=3600, pool_timeout=30, pool_pre_ping=True)
    - Create `async_sessionmaker` with `expire_on_commit=False`
    - Create declarative `Base` for SQLAlchemy models
    - Implement `get_db()` dependency that yields async session with proper cleanup
    - _Requirements: 9.1, 9.2, 9.3, 9.4_
  
  - [ ]* 2.2 Write property test for database session cleanup
    - Test that sessions are properly closed after request completion
    - Verify no connection leaks occur
    - _Requirements: 9.4_

- [ ] 3. Set up Alembic and create database models
  - [ ] 3.1 Initialize Alembic for database migrations
    - Run `alembic init alembic` to create migration directory
    - Configure `alembic.ini` to use async database URL from environment
    - Update `alembic/env.py` to import SQLAlchemy models and use async engine
    - _Requirements: 2.5, 3.3_
  
  - [ ] 3.2 Create Event model and initial migration
    - Implement `backend/app/models/event.py` with Event model: event_id (PK), name, event_date, created_at, updated_at
    - Create relationship to photos with cascade delete
    - Generate migration: `alembic revision --autogenerate -m "create events table"`
    - _Requirements: 2.1, 2.4_
  
  - [ ] 3.3 Create Photo model and migration
    - Implement `backend/app/models/photo.py` with Photo model: photo_id (PK), event_id (FK), file_path, metadata (JSONB), uploaded_at
    - Create relationships to Event and FaceEmbedding with cascade delete
    - Add index on event_id
    - Generate migration: `alembic revision --autogenerate -m "create photos table"`
    - _Requirements: 2.2, 2.4, 2.6, 2.7_
  
  - [ ] 3.4 Create FaceEmbedding model with pgvector and migration
    - Create migration to enable pgvector extension: `CREATE EXTENSION IF NOT EXISTS vector`
    - Implement `backend/app/models/face_embedding.py` with FaceEmbedding model: embedding_id (PK), photo_id (FK), embedding_vector (Vector(512)), bounding_box (JSONB), confidence_score, created_at
    - Create relationship to Photo
    - Add index on photo_id
    - Create HNSW index on embedding_vector with parameters m=16, ef_construction=200
    - Generate migration: `alembic revision --autogenerate -m "create face_embeddings table with pgvector"`
    - _Requirements: 2.3, 2.4, 2.6, 2.7, 3.1, 3.2, 3.3, 3.4, 3.5_

- [ ] 4. Implement configuration management
  - Create `backend/app/config.py` with Pydantic Settings class
  - Define settings for DATABASE_URL, STORAGE_PATH, MAX_FILE_SIZE, MAX_DIMENSION, RESIZE_THRESHOLD, CORS_ORIGINS, LOG_LEVEL, DEBUG
  - Implement validation that ensures required environment variables are present
  - Load settings from .env file using python-dotenv
  - _Requirements: 1.2, 1.5_

- [ ] 5. Implement custom exceptions
  - Create `backend/app/exceptions.py` with custom exception classes
  - Implement AppException base class with message and code attributes
  - Create ValidationError, EventNotFoundError, FaceDetectionError, DatabaseError subclasses
  - _Requirements: 7.3_

- [ ] 6. Implement logging configuration
  - [ ] 6.1 Create structured logging setup
    - Implement `backend/app/logging_config.py` with JSON formatter using python-json-logger
    - Configure log format to include timestamp, level, name, message, request_id
    - Set up logging to stdout with configurable log level from environment
    - _Requirements: 7.1, 7.2, 7.4, 7.7_
  
  - [ ] 6.2 Implement request ID middleware
    - Create `backend/app/middleware/request_id.py` with RequestIDMiddleware
    - Generate or extract X-Request-ID from headers
    - Attach request_id to request.state
    - Add X-Request-ID to response headers
    - _Requirements: 7.5, 11.2_

- [ ] 7. Implement image validation service
  - [ ] 7.1 Create ImageValidator class
    - Implement `backend/app/services/image_validator.py` with ImageValidator class
    - Implement `validate_and_prepare()` method that validates file size (≤10MB), format (JPEG/PNG/WEBP by header), dimensions (≤8000x8000)
    - Use `filetype` library to validate format by header inspection, not extension
    - Implement image resizing for images >2048px using Pillow thumbnail with LANCZOS resampling
    - Return validated image object, format, and original size
    - Raise ValidationError with specific messages for each validation failure
    - _Requirements: 10.1, 10.2, 10.3, 10.6, 10.7_
  
  - [ ]* 7.2 Write property test for file size validation
    - **Property 1: File Size Validation**
    - **Validates: Requirements 10.1**
    - Generate files of varying sizes (0-20MB)
    - Verify files >10MB are rejected, files ≤10MB pass size validation
  
  - [ ]* 7.3 Write property test for image dimension validation
    - **Property 2: Image Dimension Validation**
    - **Validates: Requirements 10.2**
    - Generate images with varying dimensions
    - Verify images >8000px in any dimension are rejected
  
  - [ ]* 7.4 Write property test for format header validation
    - **Property 3: Format Header Validation**
    - **Validates: Requirements 10.3, 5.10**
    - Create valid JPEG/PNG/WEBP images with wrong file extensions
    - Verify validation passes based on header, not extension
    - Create files with non-image headers
    - Verify validation fails regardless of extension
  
  - [ ]* 7.5 Write property test for image resizing threshold
    - **Property 6: Image Resizing Threshold**
    - **Validates: Requirements 10.6**
    - Generate images with varying dimensions around 2048px threshold
    - Verify images >2048px are resized, images ≤2048px unchanged
    - Verify aspect ratio maintained after resizing

- [ ] 8. Implement file storage service
  - [ ] 8.1 Create FileStorageService class
    - Implement `backend/app/services/file_storage.py` with FileStorageService
    - Create base storage directory on initialization
    - Implement `save_image()` method that creates event-specific subdirectories, generates UUID-based filenames, saves images to disk, returns relative path
    - Implement `get_full_path()` method to convert relative to absolute paths
    - Sanitize filenames to prevent directory traversal attacks
    - _Requirements: 5.2, 10.4, 10.5_
  
  - [ ]* 8.2 Write property test for filename sanitization
    - **Property 4: Filename Sanitization**
    - **Validates: Requirements 10.4**
    - Generate filenames with directory traversal sequences (../, ..\, absolute paths)
    - Verify sanitized filenames contain no path separators
  
  - [ ]* 8.3 Write property test for filename uniqueness
    - **Property 5: Filename Uniqueness**
    - **Validates: Requirements 10.5**
    - Generate multiple concurrent filename requests
    - Verify all generated filenames are distinct

- [ ] 9. Implement InsightFace integration
  - [ ] 9.1 Create FaceRecognitionService class
    - Implement `backend/app/services/face_service.py` with FaceRecognitionService
    - Initialize InsightFace FaceAnalysis with buffalo_l model and CPUExecutionProvider
    - Configure detection size to 640x640
    - Implement `detect_faces()` async method that loads image with cv2, runs face detection, returns list of Face objects with bounding boxes
    - Implement `extract_embedding()` method that returns 512-dimensional embedding from face object
    - Add error handling that logs failures without crashing
    - Create module-level singleton instance
    - Implement `get_face_service()` dependency
    - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5, 4.6, 4.7_
  
  - [ ]* 9.2 Write integration test for face detection
    - Test face detection on sample images with 0, 1, and multiple faces
    - Verify bounding boxes and confidence scores are returned
    - Test error handling when invalid image path provided

- [ ] 10. Implement photo repository
  - [ ] 10.1 Create PhotoRepository class
    - Implement `backend/app/repositories/photo_repository.py` with PhotoRepository
    - Accept AsyncSession in __init__
    - Implement `create_photo()` method that inserts Photo record and returns with photo_id (use flush to get ID)
    - Implement `create_face_embeddings()` method that batch inserts FaceEmbedding records
    - Implement `get_event()` method to verify event exists
    - _Requirements: 2.4, 5.5_
  
  - [ ] 10.2 Implement face similarity search
    - Add `search_similar_faces()` method to PhotoRepository
    - Use SQLAlchemy query with pgvector cosine_distance operator: `1 - cosine_distance(embedding_vector, query_embedding)`
    - Filter by event_id and similarity threshold
    - Order by similarity descending
    - Limit results to 100
    - Return photo_id, file_path, bounding_box, similarity_score
    - _Requirements: 6.4, 6.5, 6.11_
  
  - [ ]* 10.3 Write property test for search results ordering
    - **Property 8: Search Results Ordering**
    - **Validates: Requirements 6.5**
    - Generate mock search results with random similarity scores
    - Verify results are sorted in descending order by similarity
  
  - [ ]* 10.4 Write property test for search results limit
    - **Property 9: Search Results Limit**
    - **Validates: Requirements 6.11**
    - Generate search results exceeding 100 matches
    - Verify returned results never exceed 100 items

- [ ] 11. Implement photo upload service
  - [ ] 11.1 Create PhotoService class
    - Implement `backend/app/services/photo_service.py` with PhotoService
    - Accept PhotoRepository, ImageValidator, FileStorageService, FaceRecognitionService in __init__
    - Implement `upload_photo()` method that orchestrates: validate image, save to disk, create photo record, detect faces, extract embeddings, create face_embedding records
    - Return photo_id, face_count, file_path
    - Add try-catch around face detection to log errors without rolling back photo record
    - Return warning in response if face detection fails
    - _Requirements: 5.2, 5.3, 5.4, 5.5, 4.7_
  
  - [ ]* 11.2 Write integration test for photo upload workflow
    - Test complete upload workflow with sample image containing faces
    - Verify photo record and face_embedding records created in database
    - Test upload with image containing no faces
    - Test error handling when event_id doesn't exist

- [ ] 12. Checkpoint - Ensure all tests pass
  - Run all property tests and integration tests written so far
  - Verify database migrations apply cleanly
  - Ensure all tests pass, ask the user if questions arise

- [ ] 13. Implement exception handlers
  - Create `backend/app/api/exception_handlers.py` with FastAPI exception handlers
  - Implement handlers for ValidationError (400), EventNotFoundError (404), DatabaseError (503), generic Exception (500)
  - Each handler returns JSON response with success=False, message, error object with code
  - Log errors with request_id context
  - Ensure 500 errors don't expose internal details
  - Add Retry-After header to 503 responses
  - _Requirements: 7.1, 7.2, 7.3, 7.6, 8.2, 8.6_

- [ ] 14. Implement API response models
  - Create `backend/app/api/schemas.py` with Pydantic response models
  - Implement BaseResponse with success, message fields
  - Implement SuccessResponse[T] with data field
  - Implement ErrorResponse with error field containing code and details
  - Implement PhotoUploadResponse, PhotoSearchResponse models
  - Use snake_case for all field names
  - _Requirements: 8.1, 8.3, 8.4, 8.5, 8.6, 8.7_

- [ ]* 15. Write property test for API response structure
  - **Property 10: API Response Structure**
  - **Validates: Requirements 5.6, 6.7, 8.1, 8.2, 8.3, 8.4, 8.5, 8.6, 8.7**
  - Generate various success and error responses
  - Verify all contain success, message fields
  - Verify success responses contain data field
  - Verify error responses contain error field with code
  - Verify all field names use snake_case

- [ ] 16. Implement photo upload API endpoint
  - [ ] 16.1 Create photo upload route
    - Create `backend/app/api/routes/photos.py` with FastAPI router
    - Implement POST `/api/photos/upload` endpoint accepting multipart/form-data with file and event_id
    - Use dependency injection for db session and PhotoService
    - Call photo_service.upload_photo(), commit transaction on success
    - Return 201 status with PhotoUploadResponse
    - Handle ValidationError (400), EventNotFoundError (404) with appropriate responses
    - Return warning message if no faces detected (5.9)
    - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5, 5.6, 5.7, 5.8, 5.9_
  
  - [ ]* 16.2 Write integration test for upload endpoint edge cases
    - Test upload with non-existent event_id returns 404
    - Test upload with invalid image format returns 400
    - Test upload with oversized file returns 400
    - Test upload with image containing no faces stores photo but returns warning

- [ ] 17. Implement face search functionality
  - [ ] 17.1 Create face selection logic helper
    - Implement helper function to select largest face from detected faces
    - Calculate bounding box area as (x2-x1) * (y2-y1)
    - Return face with maximum area
    - _Requirements: 6.8_
  
  - [ ]* 17.2 Write property test for largest face selection
    - **Property 7: Largest Face Selection**
    - **Validates: Requirements 6.8**
    - Generate sets of faces with varying bounding box sizes
    - Verify selected face has largest area
  
  - [ ] 17.3 Implement face search endpoint
    - Add POST `/api/photos/search` endpoint to photos router
    - Accept multipart/form-data with selfie file, event_id, optional threshold (default 0.6)
    - Save selfie to temporary file, detect faces using face_service
    - Return 400 if no face detected
    - Select largest face if multiple detected
    - Generate embedding for selected face
    - Call photo_repo.search_similar_faces() with query embedding
    - Return PhotoSearchResponse with matches array containing photo_id, file_path, bounding_box, similarity_score
    - Clean up temporary file after processing
    - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5, 6.6, 6.7, 6.8, 6.9, 6.10, 6.11_
  
  - [ ]* 17.4 Write integration test for search endpoint
    - Test search with selfie returns matching photos
    - Test search with no face detected returns 400
    - Test search with non-existent event_id returns 404
    - Test similarity threshold filtering
    - Test results limited to 100

- [ ] 18. Implement health check endpoint
  - Create GET `/health` endpoint in photos router
  - Check database connectivity by executing simple query
  - Return 200 with status=healthy if database connected
  - Return 503 with status=unhealthy if database connection fails
  - _Requirements: 9.5_

- [ ] 19. Implement FastAPI application setup
  - [ ] 19.1 Create main FastAPI application
    - Create `backend/app/main.py` with FastAPI app initialization
    - Set API metadata (title="AI Wedding Photo Portal", version="1.0.0", description)
    - Enable CORS middleware with configurable allowed origins from settings
    - Add RequestIDMiddleware
    - Register exception handlers
    - Include photos router with /api prefix
    - Add startup event handler to validate environment and load InsightFace model
    - Configure request size limits (max 11MB for 10MB images + overhead)
    - _Requirements: 1.5, 11.1, 11.2, 11.3, 11.4, 11.5, 11.7_
  
  - [ ] 19.2 Create application entry point
    - Create `backend/app/__init__.py` to mark as package
    - Create `backend/run.py` to run uvicorn server
    - Add command: `uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload`
    - _Requirements: 1.4_

- [ ] 20. Implement property test for confidence score extraction
  - **Property 11: Confidence Score Extraction**
  - **Validates: Requirements 4.6**
  - Mock InsightFace face objects with various det_score values
  - Verify stored confidence_score matches det_score as Python float

- [ ] 21. Implement property test for invalid format rejection
  - **Property 12: Invalid Format Rejection**
  - **Validates: Requirements 5.8**
  - Create files with non-image headers (text, PDF, executable)
  - Verify upload returns 400 error with format information

- [ ] 22. Add comprehensive integration tests
  - [ ]* 22.1 Write end-to-end test for photo upload and search workflow
    - Upload sample photos with faces to test event
    - Upload selfie matching one of the photos
    - Verify search returns the correct photos with high similarity scores
    - Test that photos from different events are not returned
  
  - [ ]* 22.2 Write integration test for database connection pool
    - Test concurrent requests to verify connection pooling works
    - Test connection recycling after pool_recycle timeout
    - Test pool exhaustion handling returns 503
  
  - [ ]* 22.3 Write integration test for cascade delete behavior
    - Create photo with face_embeddings
    - Delete photo record
    - Verify face_embeddings automatically deleted
    - _Requirements: 2.6_

- [ ] 23. Create seed data script
  - Create `backend/scripts/seed_data.py` to create sample events
  - Add command to create test event: "Test Wedding 2024"
  - Document in README how to run seed script
  - _Optional but helpful for development and testing_

- [ ] 24. Final checkpoint - Complete testing and documentation
  - Run full test suite with coverage report
  - Verify all property tests pass with 100+ iterations
  - Verify all integration tests pass
  - Review README for completeness (setup, migrations, running server, running tests)
  - Ensure .env.example includes all required variables
  - Ensure all tests pass, ask the user if questions arise

## Notes

- Tasks marked with `*` are optional test tasks and can be skipped for faster MVP deployment, but are highly recommended for production readiness
- The implementation uses Python with FastAPI, SQLAlchemy 2.0 async, and PostgreSQL with pgvector
- Property-based tests use Hypothesis library to verify correctness properties across many input variations
- Each task references specific requirements for traceability
- Checkpoints ensure incremental validation and allow for user feedback
- InsightFace buffalo_l model is loaded once at startup and reused for all requests
- Database connection pooling prevents connection exhaustion under load
- All API responses follow consistent structure with success, message, and data/error fields
- File validation prevents security issues like directory traversal and format spoofing
- Face detection failures don't crash the system - photos are stored even if face detection fails

## Task Dependency Graph

```json
{
  "waves": [
    { "id": 0, "tasks": ["1", "4", "5"] },
    { "id": 1, "tasks": ["2.1", "3.1"] },
    { "id": 2, "tasks": ["2.2", "3.2"] },
    { "id": 3, "tasks": ["3.3"] },
    { "id": 4, "tasks": ["3.4", "6.1"] },
    { "id": 5, "tasks": ["6.2", "7.1"] },
    { "id": 6, "tasks": ["7.2", "7.3", "7.4", "7.5", "8.1"] },
    { "id": 7, "tasks": ["8.2", "8.3", "9.1"] },
    { "id": 8, "tasks": ["9.2", "10.1"] },
    { "id": 9, "tasks": ["10.2"] },
    { "id": 10, "tasks": ["10.3", "10.4", "11.1"] },
    { "id": 11, "tasks": ["11.2", "13", "14"] },
    { "id": 12, "tasks": ["15", "16.1"] },
    { "id": 13, "tasks": ["16.2", "17.1"] },
    { "id": 14, "tasks": ["17.2", "17.3"] },
    { "id": 15, "tasks": ["17.4", "18", "19.1"] },
    { "id": 16, "tasks": ["19.2", "20", "21"] },
    { "id": 17, "tasks": ["22.1", "22.2", "22.3", "23"] }
  ]
}
```
