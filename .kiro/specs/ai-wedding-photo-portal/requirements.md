# Requirements Document

## Introduction

The AI-Powered Wedding Photo Portal is a FastAPI-based backend system that enables automatic face recognition and photo matching at wedding events. The system allows guests to upload a selfie and instantly discover all photos containing their face from the event. The backend uses InsightFace for face detection and embedding generation, PostgreSQL with pgvector for efficient similarity search, and provides RESTful API endpoints for photo upload and face-based search operations.

## Glossary

- **Backend_System**: The FastAPI application providing photo upload and search capabilities
- **Database**: PostgreSQL database with pgvector extension for vector similarity search
- **Face_Detector**: InsightFace buffalo_l model component that detects faces in images
- **Embedding_Generator**: InsightFace component that generates 512-dimensional face embeddings
- **Photo_Upload_Endpoint**: REST API endpoint accepting image uploads
- **Search_Endpoint**: REST API endpoint accepting selfie images and returning matching photos
- **Event**: A wedding or celebration for which photos are being collected
- **Photo**: An uploaded image file associated with an event
- **Face_Embedding**: A 512-dimensional vector representation of a detected face
- **Similarity_Search**: Cosine similarity-based vector search using pgvector
- **Migration_System**: Alembic database migration management system
- **ORM**: SQLAlchemy 2.0 Object-Relational Mapping layer

## Requirements

### Requirement 1: Project Structure and Environment Setup

**User Story:** As a developer, I want a well-organized FastAPI project structure with proper environment management, so that the application is maintainable and configuration is secure.

#### Acceptance Criteria

1. THE Backend_System SHALL be organized in a backend folder with separate modules for API routes, database models, services, and configuration
2. THE Backend_System SHALL load configuration from environment variables using a .env file
3. THE Backend_System SHALL provide a requirements.txt file listing all Python dependencies with pinned versions
4. THE Backend_System SHALL include a README.md with setup and run instructions
5. WHEN the application starts, THE Backend_System SHALL validate that all required environment variables are present

### Requirement 2: Database Schema and Models

**User Story:** As a developer, I want properly designed database models with migration support, so that data is structured efficiently and schema changes are version-controlled.

#### Acceptance Criteria

1. THE Database SHALL include an events table with fields for event_id, name, date, and timestamps
2. THE Database SHALL include a photos table with fields for photo_id, event_id (foreign key), file_path, upload_timestamp, and metadata
3. THE Database SHALL include a face_embeddings table with fields for embedding_id, photo_id (foreign key), embedding_vector (using pgvector), bounding_box coordinates, and confidence_score
4. THE ORM SHALL use SQLAlchemy 2.0 declarative models for all database tables
5. THE Migration_System SHALL manage all database schema changes using Alembic
6. WHEN a photo is deleted, THE Database SHALL cascade delete all associated face_embeddings records
7. THE Database SHALL create indexes on event_id and photo_id foreign key columns for query performance

### Requirement 3: PostgreSQL and pgvector Configuration

**User Story:** As a system administrator, I want PostgreSQL configured with pgvector extension, so that efficient vector similarity search is available.

#### Acceptance Criteria

1. THE Database SHALL use PostgreSQL as the relational database engine
2. THE Database SHALL enable the pgvector extension for vector operations
3. THE Migration_System SHALL include a migration that creates the pgvector extension if it doesn't exist
4. THE face_embeddings table SHALL use the vector data type with 512 dimensions for storing embeddings
5. THE Database SHALL create a pgvector index on the embedding_vector column for efficient similarity search

### Requirement 4: InsightFace Integration

**User Story:** As a developer, I want InsightFace integrated with the buffalo_l model, so that faces can be detected and encoded into embeddings.

#### Acceptance Criteria

1. THE Backend_System SHALL use the InsightFace library with the buffalo_l model
2. THE Backend_System SHALL configure InsightFace to use ONNX Runtime CPU provider
3. WHEN the application starts, THE Backend_System SHALL load the buffalo_l model into memory
4. THE Face_Detector SHALL detect all faces in an uploaded image with bounding box coordinates
5. THE Embedding_Generator SHALL generate a 512-dimensional embedding vector for each detected face
6. THE Backend_System SHALL include confidence scores for each detected face
7. IF face detection fails for an image, THEN THE Backend_System SHALL log the error and continue processing without crashing

### Requirement 5: Photo Upload API Endpoint

**User Story:** As a guest, I want to upload photos to an event, so that my photos are added to the event collection and become searchable by face.

#### Acceptance Criteria

1. THE Photo_Upload_Endpoint SHALL accept HTTP POST requests with multipart/form-data containing an image file and event_id
2. WHEN a valid image is uploaded, THE Photo_Upload_Endpoint SHALL save the image file to the configured storage directory
3. WHEN an image is saved, THE Backend_System SHALL detect all faces in the image using the Face_Detector
4. WHEN faces are detected, THE Backend_System SHALL generate embeddings for each face using the Embedding_Generator
5. WHEN embeddings are generated, THE Backend_System SHALL store the photo record and all face_embedding records in the Database
6. THE Photo_Upload_Endpoint SHALL return a JSON response with photo_id, number of faces detected, and upload status
7. IF the event_id does not exist, THEN THE Photo_Upload_Endpoint SHALL return a 404 error with a descriptive message
8. IF the uploaded file is not a valid image format, THEN THE Photo_Upload_Endpoint SHALL return a 400 error with a descriptive message
9. IF no faces are detected in the image, THEN THE Photo_Upload_Endpoint SHALL store the photo record but return a warning in the response
10. THE Photo_Upload_Endpoint SHALL support JPEG, PNG, and WEBP image formats

### Requirement 6: Face Search API Endpoint

**User Story:** As a guest, I want to upload a selfie and find all photos containing my face, so that I can discover and download photos of myself from the event.

#### Acceptance Criteria

1. THE Search_Endpoint SHALL accept HTTP POST requests with multipart/form-data containing a selfie image and event_id
2. WHEN a valid selfie is uploaded, THE Search_Endpoint SHALL detect the primary face using the Face_Detector
3. WHEN a face is detected, THE Search_Endpoint SHALL generate an embedding using the Embedding_Generator
4. WHEN an embedding is generated, THE Search_Endpoint SHALL perform cosine similarity search against all face_embeddings for the specified event using pgvector
5. THE Similarity_Search SHALL return face matches ordered by similarity score in descending order
6. THE Search_Endpoint SHALL include a similarity threshold parameter with a default value of 0.6
7. THE Search_Endpoint SHALL return a JSON response containing an array of matching photos with photo_id, file_path, similarity_score, and face bounding_box
8. IF multiple faces are detected in the selfie, THEN THE Search_Endpoint SHALL use the largest face by bounding box area
9. IF no face is detected in the selfie, THEN THE Search_Endpoint SHALL return a 400 error with a descriptive message
10. IF the event_id does not exist, THEN THE Search_Endpoint SHALL return a 404 error with a descriptive message
11. THE Search_Endpoint SHALL limit results to a maximum of 100 photos per request

### Requirement 7: Error Handling and Logging

**User Story:** As a developer, I want comprehensive error handling and logging, so that issues can be diagnosed and the system remains stable.

#### Acceptance Criteria

1. THE Backend_System SHALL log all API requests with timestamp, endpoint, and request_id
2. THE Backend_System SHALL log all errors with full stack traces and context information
3. WHEN an unhandled exception occurs, THE Backend_System SHALL return a 500 error with a generic message without exposing internal details
4. THE Backend_System SHALL use structured logging with log levels (DEBUG, INFO, WARNING, ERROR, CRITICAL)
5. THE Backend_System SHALL include request correlation IDs in all log entries for request tracing
6. IF database connection fails, THEN THE Backend_System SHALL log the error and return a 503 Service Unavailable error
7. THE Backend_System SHALL configure logging output format to include timestamp, level, module, and message

### Requirement 8: API Response Standards

**User Story:** As a frontend developer, I want consistent API response formats, so that response handling is predictable and reliable.

#### Acceptance Criteria

1. THE Backend_System SHALL return all successful responses with HTTP 2xx status codes and JSON body
2. THE Backend_System SHALL return all error responses with appropriate HTTP 4xx or 5xx status codes and JSON body
3. THE Backend_System SHALL include a "success" boolean field in all JSON responses
4. THE Backend_System SHALL include a "message" field with human-readable description in all JSON responses
5. THE Backend_System SHALL include a "data" field containing the response payload in successful responses
6. THE Backend_System SHALL include an "error" field containing error details in error responses
7. THE Backend_System SHALL use consistent field naming convention (snake_case) across all responses

### Requirement 9: Database Connection Management

**User Story:** As a system administrator, I want efficient database connection management, so that database resources are used efficiently and connections are properly pooled.

#### Acceptance Criteria

1. THE Backend_System SHALL use SQLAlchemy connection pooling for database connections
2. THE Backend_System SHALL configure connection pool size based on environment variables with sensible defaults
3. THE Backend_System SHALL configure connection pool timeout and recycle settings
4. WHEN a database connection is acquired for a request, THE Backend_System SHALL return it to the pool after the request completes
5. THE Backend_System SHALL implement health check endpoint that verifies database connectivity
6. IF the database connection pool is exhausted, THEN THE Backend_System SHALL return a 503 error with retry-after header

### Requirement 10: Image Processing and Validation

**User Story:** As a developer, I want robust image processing and validation, so that invalid or malicious files are rejected and valid images are processed correctly.

#### Acceptance Criteria

1. THE Backend_System SHALL validate image file size with a maximum limit of 10MB
2. THE Backend_System SHALL validate image dimensions with a maximum of 8000x8000 pixels
3. THE Backend_System SHALL verify image file format by reading file headers, not just file extensions
4. WHEN an image is uploaded, THE Backend_System SHALL sanitize the filename to prevent directory traversal attacks
5. THE Backend_System SHALL generate unique filenames for stored images using UUID or hash-based naming
6. THE Backend_System SHALL resize images larger than 2048x2048 pixels before face detection to optimize performance
7. IF an image fails validation, THEN THE Backend_System SHALL return a 400 error with specific validation failure reason

### Requirement 11: FastAPI Application Configuration

**User Story:** As a developer, I want FastAPI properly configured with middleware and documentation, so that the API is production-ready and well-documented.

#### Acceptance Criteria

1. THE Backend_System SHALL enable CORS middleware with configurable allowed origins
2. THE Backend_System SHALL enable request ID middleware for request tracing
3. THE Backend_System SHALL enable automatic OpenAPI documentation at /docs endpoint
4. THE Backend_System SHALL include API metadata (title, version, description) in OpenAPI schema
5. THE Backend_System SHALL configure request size limits to prevent memory exhaustion
6. THE Backend_System SHALL include proper HTTP response models in all endpoint definitions
7. THE Backend_System SHALL use FastAPI dependency injection for database session management

---

## Notes

This requirements document focuses on the core backend functionality for the AI-powered wedding photo portal. The system is designed to be production-ready with proper error handling, logging, validation, and security considerations. Authentication, authorization, caching (Redis), background job processing (Celery), and object storage (Cloudflare R2) are explicitly excluded from this initial implementation and may be added in future phases.

The face detection and embedding generation using InsightFace buffalo_l model is the core AI functionality that enables the photo matching feature. The pgvector extension provides efficient similarity search capabilities essential for real-time photo discovery.
