# Design Document: AI-Powered Wedding Photo Portal Backend

## Overview

The AI-powered wedding photo portal backend is a FastAPI-based REST API that enables face-based photo discovery at wedding events. The system processes uploaded photos through face detection and embedding generation, stores facial features in a PostgreSQL database with pgvector, and provides a similarity search API that allows guests to find photos of themselves using a selfie.

### Core Capabilities

- **Photo Upload with Face Detection**: Accept event photos, detect all faces using InsightFace, generate 512-dimensional embeddings, and store them for efficient similarity search
- **Face-Based Search**: Accept a selfie, extract facial features, and perform cosine similarity search to find all matching photos from an event
- **Scalable Vector Search**: Leverage pgvector with HNSW indexing for sub-20ms p95 query latency on datasets with millions of embeddings
- **Production-Ready API**: Structured error handling, request tracing, comprehensive logging, and OpenAPI documentation

### Technology Stack

- **Web Framework**: FastAPI 0.115+ (async endpoints, dependency injection, automatic OpenAPI docs)
- **ORM**: SQLAlchemy 2.0+ (async session support, declarative models)
- **Database**: PostgreSQL 15+ with pgvector 0.5+ extension (vector similarity search)
- **Face Recognition**: InsightFace buffalo_l model via ONNX Runtime CPU provider
- **Image Processing**: Pillow 10+ (validation, resizing, format verification)
- **Migrations**: Alembic 1.13+ (schema version control)
- **Validation**: Pydantic v2 (request/response models, configuration management)

### Design Principles

1. **Async-First**: All I/O operations (database, file system, face processing) use async/await to maximize concurrency
2. **Dependency Injection**: Database sessions, InsightFace model, and configuration managed via FastAPI dependencies
3. **Fail-Safe**: Face detection failures on individual photos do not crash the API; errors are logged and gracefully handled
4. **Explicit Schema**: All database models use SQLAlchemy 2.0 declarative syntax; all API endpoints define Pydantic request/response models
5. **Security**: File validation by header inspection, filename sanitization, size limits, and dimension constraints

## Architecture

### System Architecture

```mermaid
graph TB
    Client[Client Application]
    API[FastAPI Application]
    DB[(PostgreSQL + pgvector)]
    FS[File Storage]
    IF[InsightFace buffalo_l]
    
    Client -->|HTTP POST /api/photos/upload| API
    Client -->|HTTP POST /api/photos/search| API
    API -->|Query/Insert| DB
    API -->|Save Images| FS
    API -->|Face Detection & Embedding| IF
    IF -->|ONNX Runtime CPU| IF
    
    subgraph Backend System
        API
        IF
    end
    
    subgraph Data Layer
        DB
        FS
    end
```

### Request Flow: Photo Upload

```mermaid
sequenceDiagram
    participant Client
    participant API as FastAPI Endpoint
    participant Val as Image Validator
    participant FS as File Storage
    participant IF as InsightFace
    participant DB as PostgreSQL
    
    Client->>API: POST /api/photos/upload<br/>(image, event_id)
    API->>Val: Validate image<br/>(size, format, dimensions)
    Val-->>API: Validation result
    alt Invalid image
        API-->>Client: 400 Bad Request
    end
    API->>FS: Save image to disk<br/>(UUID filename)
    FS-->>API: File path
    API->>IF: Detect faces
    IF-->>API: Faces with bounding boxes
    API->>IF: Generate embeddings<br/>for each face
    IF-->>API: 512-dim embeddings
    API->>DB: INSERT photo record
    API->>DB: INSERT face_embeddings<br/>(batch)
    DB-->>API: Commit success
    API-->>Client: 201 Created<br/>(photo_id, face_count)
```

### Request Flow: Face Search

```mermaid
sequenceDiagram
    participant Client
    participant API as FastAPI Endpoint
    participant IF as InsightFace
    participant DB as PostgreSQL + pgvector
    
    Client->>API: POST /api/photos/search<br/>(selfie, event_id, threshold)
    API->>IF: Detect primary face
    IF-->>API: Face bounding box
    alt No face detected
        API-->>Client: 400 Bad Request
    end
    API->>IF: Generate embedding
    IF-->>API: 512-dim query embedding
    API->>DB: SELECT with cosine similarity<br/>ORDER BY similarity DESC<br/>LIMIT 100
    DB-->>API: Matching photos with scores
    API-->>Client: 200 OK<br/>(photo array with similarity)
```

### Component Layering

```
┌─────────────────────────────────────────┐
│         API Routes (Endpoints)          │  ← FastAPI router definitions
├─────────────────────────────────────────┤
│       Services (Business Logic)         │  ← Photo service, face service
├─────────────────────────────────────────┤
│    Repositories (Data Access Layer)     │  ← SQLAlchemy queries
├─────────────────────────────────────────┤
│         Models (Database Schema)        │  ← SQLAlchemy ORM models
└─────────────────────────────────────────┘

┌─────────────────────────────────────────┐
│      Cross-Cutting Concerns             │
├─────────────────────────────────────────┤
│  • Logging (request ID, structured)     │
│  • Error handling (exception handlers)  │
│  • Validation (Pydantic schemas)        │
│  • Configuration (environment vars)     │
└─────────────────────────────────────────┘
```

## Components and Interfaces

### 1. Database Session Management

**Purpose**: Provide request-scoped async database sessions via dependency injection

**Implementation**:
```python
# backend/app/database.py

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import declarative_base

engine = create_async_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,
    pool_size=20,
    max_overflow=40,
    pool_recycle=3600,
    pool_timeout=30,
    echo=settings.DEBUG
)

async_session_factory = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False
)

Base = declarative_base()

async def get_db() -> AsyncSession:
    """Dependency that provides a database session."""
    async with async_session_factory() as session:
        try:
            yield session
        finally:
            await session.close()
```

**Key Design Decisions**:
- Pool size configured for production load (20 base + 40 overflow = 60 max concurrent connections)
- `pool_pre_ping=True` ensures stale connections are detected before use
- `pool_recycle=3600` refreshes connections hourly to prevent PostgreSQL idle timeout
- `expire_on_commit=False` allows access to loaded objects after commit without refetching

### 2. InsightFace Model Management

**Purpose**: Load buffalo_l model once at startup and provide it as a dependency

**Implementation**:
```python
# backend/app/services/face_service.py

import insightface
from insightface.app import FaceAnalysis

class FaceRecognitionService:
    def __init__(self):
        self.app = FaceAnalysis(
            name='buffalo_l',
            providers=['CPUExecutionProvider']
        )
        self.app.prepare(ctx_id=0, det_size=(640, 640))
    
    async def detect_faces(self, image_path: str) -> List[Face]:
        """Detect all faces in image and return with bounding boxes."""
        img = cv2.imread(image_path)
        faces = self.app.get(img)
        return faces
    
    def extract_embedding(self, face) -> np.ndarray:
        """Extract 512-dimensional embedding from detected face."""
        return face.embedding

# Global instance
face_service = FaceRecognitionService()

async def get_face_service() -> FaceRecognitionService:
    """Dependency that provides the face recognition service."""
    return face_service
```

**Key Design Decisions**:
- Model loaded once at module import (application startup) to avoid repeated disk I/O
- Detection size of 640×640 balances accuracy and performance for typical wedding photos
- CPU provider selected per requirements (no GPU dependency)
- Embeddings are normalized 512-dimensional vectors suitable for cosine similarity

### 3. Image Validation Service

**Purpose**: Validate uploaded images for security and compatibility

**Implementation**:
```python
# backend/app/services/image_validator.py

from PIL import Image
import filetype

class ImageValidator:
    MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
    MAX_DIMENSION = 8000
    RESIZE_THRESHOLD = 2048
    ALLOWED_FORMATS = {'jpeg', 'png', 'webp'}
    
    async def validate_and_prepare(self, file: UploadFile) -> dict:
        """Validate image and return prepared image info."""
        # Read file content
        content = await file.read()
        await file.seek(0)
        
        # Validate size
        if len(content) > self.MAX_FILE_SIZE:
            raise ValidationError("File exceeds 10MB limit")
        
        # Validate format by header inspection
        kind = filetype.guess(content)
        if not kind or kind.extension not in self.ALLOWED_FORMATS:
            raise ValidationError(f"Invalid image format. Allowed: {self.ALLOWED_FORMATS}")
        
        # Open and validate dimensions
        try:
            img = Image.open(BytesIO(content))
        except Exception:
            raise ValidationError("Corrupted image file")
        
        width, height = img.size
        if width > self.MAX_DIMENSION or height > self.MAX_DIMENSION:
            raise ValidationError(f"Image dimensions exceed {self.MAX_DIMENSION}px")
        
        # Resize if needed for face detection optimization
        if width > self.RESIZE_THRESHOLD or height > self.RESIZE_THRESHOLD:
            img.thumbnail((self.RESIZE_THRESHOLD, self.RESIZE_THRESHOLD), Image.Resampling.LANCZOS)
        
        return {
            "image": img,
            "format": kind.extension,
            "original_size": (width, height)
        }
```

**Key Design Decisions**:
- Header-based validation using `filetype` library prevents format spoofing via file extensions
- Images larger than 2048px are resized before face detection to reduce processing time
- Pillow thumbnail maintains aspect ratio using LANCZOS resampling for quality
- Validation failures return specific error messages for client debugging

### 4. File Storage Service

**Purpose**: Save uploaded images with secure, unique filenames

**Implementation**:
```python
# backend/app/services/file_storage.py

import uuid
from pathlib import Path
import aiofiles

class FileStorageService:
    def __init__(self, base_path: str):
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)
    
    async def save_image(self, image: Image, format: str, event_id: int) -> str:
        """Save image and return relative file path."""
        # Create event-specific subdirectory
        event_dir = self.base_path / f"event_{event_id}"
        event_dir.mkdir(exist_ok=True)
        
        # Generate unique filename
        filename = f"{uuid.uuid4()}.{format}"
        file_path = event_dir / filename
        
        # Save image
        image.save(file_path, format=format.upper())
        
        # Return relative path for database storage
        return str(file_path.relative_to(self.base_path))
    
    def get_full_path(self, relative_path: str) -> Path:
        """Convert relative path to full filesystem path."""
        return self.base_path / relative_path
```

**Key Design Decisions**:
- UUID-based filenames prevent collisions and directory traversal attacks
- Event-specific subdirectories improve file organization and filesystem performance
- Relative paths stored in database for portability (can move storage directory)
- Async file I/O prevents blocking event loop during large file writes

### 5. Photo Repository

**Purpose**: Data access layer for photo and face embedding operations

**Implementation**:
```python
# backend/app/repositories/photo_repository.py

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models import Photo, FaceEmbedding

class PhotoRepository:
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def create_photo(self, event_id: int, file_path: str, metadata: dict) -> Photo:
        """Create a new photo record."""
        photo = Photo(
            event_id=event_id,
            file_path=file_path,
            metadata=metadata
        )
        self.session.add(photo)
        await self.session.flush()  # Get photo_id for face embeddings
        return photo
    
    async def create_face_embeddings(self, photo_id: int, faces: List[dict]) -> List[FaceEmbedding]:
        """Batch create face embedding records."""
        embeddings = [
            FaceEmbedding(
                photo_id=photo_id,
                embedding_vector=face['embedding'],
                bounding_box=face['bbox'],
                confidence_score=face['confidence']
            )
            for face in faces
        ]
        self.session.add_all(embeddings)
        await self.session.flush()
        return embeddings
    
    async def search_similar_faces(
        self,
        event_id: int,
        query_embedding: np.ndarray,
        threshold: float = 0.6,
        limit: int = 100
    ) -> List[dict]:
        """Find photos with similar faces using cosine similarity."""
        query = select(
            Photo.photo_id,
            Photo.file_path,
            FaceEmbedding.bounding_box,
            (1 - FaceEmbedding.embedding_vector.cosine_distance(query_embedding)).label('similarity')
        ).join(
            FaceEmbedding, Photo.photo_id == FaceEmbedding.photo_id
        ).where(
            Photo.event_id == event_id
        ).where(
            (1 - FaceEmbedding.embedding_vector.cosine_distance(query_embedding)) >= threshold
        ).order_by(
            desc('similarity')
        ).limit(limit)
        
        result = await self.session.execute(query)
        return [
            {
                'photo_id': row.photo_id,
                'file_path': row.file_path,
                'bounding_box': row.bounding_box,
                'similarity_score': float(row.similarity)
            }
            for row in result
        ]
```

**Key Design Decisions**:
- Repository pattern isolates SQLAlchemy queries from business logic
- `flush()` instead of `commit()` allows transactional control at service layer
- Cosine similarity computed via pgvector operator: `1 - cosine_distance(v1, v2)`
- Query filters by event_id first to reduce vector comparison scope
- Results limited to 100 matches to prevent excessive data transfer

### 6. Photo Upload Service

**Purpose**: Orchestrate photo upload workflow (validation → storage → face detection → database)

**Implementation**:
```python
# backend/app/services/photo_service.py

from app.repositories.photo_repository import PhotoRepository
from app.services.image_validator import ImageValidator
from app.services.file_storage import FileStorageService
from app.services.face_service import FaceRecognitionService

class PhotoService:
    def __init__(
        self,
        photo_repo: PhotoRepository,
        image_validator: ImageValidator,
        file_storage: FileStorageService,
        face_service: FaceRecognitionService
    ):
        self.photo_repo = photo_repo
        self.image_validator = image_validator
        self.file_storage = file_storage
        self.face_service = face_service
    
    async def upload_photo(self, file: UploadFile, event_id: int) -> dict:
        """Process photo upload with face detection."""
        # Validate image
        validated = await self.image_validator.validate_and_prepare(file)
        
        # Save to disk
        file_path = await self.file_storage.save_image(
            validated['image'],
            validated['format'],
            event_id
        )
        
        # Create photo record
        photo = await self.photo_repo.create_photo(
            event_id=event_id,
            file_path=file_path,
            metadata={'original_size': validated['original_size']}
        )
        
        # Detect faces
        full_path = self.file_storage.get_full_path(file_path)
        faces = await self.face_service.detect_faces(str(full_path))
        
        # Extract embeddings and create records
        face_data = [
            {
                'embedding': self.face_service.extract_embedding(face),
                'bbox': face.bbox.tolist(),
                'confidence': float(face.det_score)
            }
            for face in faces
        ]
        
        if face_data:
            await self.photo_repo.create_face_embeddings(photo.photo_id, face_data)
        
        return {
            'photo_id': photo.photo_id,
            'face_count': len(face_data),
            'file_path': file_path
        }
```

**Key Design Decisions**:
- Service layer orchestrates multiple repositories and services
- Transaction boundary managed at service level (commit happens in endpoint)
- Face detection failures logged but don't rollback photo creation
- Metadata stored as JSON for extensibility (can add EXIF, GPS, etc.)

### 7. API Endpoints

**Photo Upload Endpoint**:
```python
# backend/app/api/routes/photos.py

@router.post("/upload", status_code=201)
async def upload_photo(
    event_id: int = Form(...),
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    photo_service: PhotoService = Depends(get_photo_service)
):
    """Upload a photo to an event with automatic face detection."""
    try:
        result = await photo_service.upload_photo(file, event_id)
        await db.commit()
        
        return {
            'success': True,
            'message': f'Photo uploaded with {result["face_count"]} faces detected',
            'data': result
        }
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except EventNotFoundError:
        raise HTTPException(status_code=404, detail=f'Event {event_id} not found')
```

**Face Search Endpoint**:
```python
@router.post("/search")
async def search_photos(
    event_id: int = Form(...),
    selfie: UploadFile = File(...),
    threshold: float = Form(0.6),
    db: AsyncSession = Depends(get_db),
    photo_repo: PhotoRepository = Depends(get_photo_repository),
    face_service: FaceRecognitionService = Depends(get_face_service)
):
    """Search for photos containing a face similar to the uploaded selfie."""
    # Detect face in selfie
    temp_path = await save_temp_file(selfie)
    faces = await face_service.detect_faces(temp_path)
    
    if not faces:
        raise HTTPException(status_code=400, detail='No face detected in selfie')
    
    # Use largest face if multiple detected
    primary_face = max(faces, key=lambda f: (f.bbox[2] - f.bbox[0]) * (f.bbox[3] - f.bbox[1]))
    query_embedding = face_service.extract_embedding(primary_face)
    
    # Search similar faces
    results = await photo_repo.search_similar_faces(
        event_id=event_id,
        query_embedding=query_embedding,
        threshold=threshold,
        limit=100
    )
    
    return {
        'success': True,
        'message': f'Found {len(results)} matching photos',
        'data': {
            'matches': results,
            'query_face_confidence': float(primary_face.det_score)
        }
    }
```

## Data Models

### Database Schema

```mermaid
erDiagram
    events ||--o{ photos : contains
    photos ||--o{ face_embeddings : has
    
    events {
        int event_id PK
        varchar name
        date event_date
        timestamp created_at
        timestamp updated_at
    }
    
    photos {
        int photo_id PK
        int event_id FK
        varchar file_path
        jsonb metadata
        timestamp uploaded_at
    }
    
    face_embeddings {
        int embedding_id PK
        int photo_id FK
        vector embedding_vector
        jsonb bounding_box
        float confidence_score
        timestamp created_at
    }
```

### SQLAlchemy Models

**Events Table**:
```python
# backend/app/models/event.py

from sqlalchemy import Column, Integer, String, Date, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base

class Event(Base):
    __tablename__ = 'events'
    
    event_id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    event_date = Column(Date, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    photos = relationship('Photo', back_populates='event', cascade='all, delete-orphan')
```

**Photos Table**:
```python
# backend/app/models/photo.py

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Index
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base

class Photo(Base):
    __tablename__ = 'photos'
    
    photo_id = Column(Integer, primary_key=True, autoincrement=True)
    event_id = Column(Integer, ForeignKey('events.event_id', ondelete='CASCADE'), nullable=False)
    file_path = Column(String(512), nullable=False)
    metadata = Column(JSONB, default={})
    uploaded_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # Relationships
    event = relationship('Event', back_populates='photos')
    face_embeddings = relationship('FaceEmbedding', back_populates='photo', cascade='all, delete-orphan')
    
    # Indexes
    __table_args__ = (
        Index('ix_photos_event_id', 'event_id'),
    )
```

**Face Embeddings Table**:
```python
# backend/app/models/face_embedding.py

from sqlalchemy import Column, Integer, Float, DateTime, ForeignKey, Index
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from pgvector.sqlalchemy import Vector
from app.database import Base

class FaceEmbedding(Base):
    __tablename__ = 'face_embeddings'
    
    embedding_id = Column(Integer, primary_key=True, autoincrement=True)
    photo_id = Column(Integer, ForeignKey('photos.photo_id', ondelete='CASCADE'), nullable=False)
    embedding_vector = Column(Vector(512), nullable=False)
    bounding_box = Column(JSONB, nullable=False)  # {'x1': float, 'y1': float, 'x2': float, 'y2': float}
    confidence_score = Column(Float, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # Relationships
    photo = relationship('Photo', back_populates='face_embeddings')
    
    # Indexes
    __table_args__ = (
        Index('ix_face_embeddings_photo_id', 'photo_id'),
        Index('ix_face_embeddings_vector_hnsw', 'embedding_vector', postgresql_using='hnsw', postgresql_with={'m': 16, 'ef_construction': 200}),
    )
```

**Key Design Decisions**:
- `ondelete='CASCADE'` ensures face embeddings are deleted when photo is removed
- JSONB used for metadata and bounding_box for flexibility and PostgreSQL JSON query support
- Vector(512) matches InsightFace buffalo_l embedding dimensionality
- HNSW index with `m=16` (connections per layer) and `ef_construction=200` (build quality) balances build time and query performance
- Timestamp columns use `timezone=True` for consistent UTC storage

### pgvector Index Configuration

**Index Type Selection**: HNSW chosen over IVFFlat because:
- Better recall (95-99% vs 80-90% for IVFFlat at similar query speeds)
- No need to rebuild when data distribution changes
- Deterministic queries (IVFFlat can miss vectors if they're in wrong cluster)

**HNSW Parameters**:
- `m=16`: Number of bi-directional links per node (higher = better recall, more memory)
- `ef_construction=200`: Size of candidate list during index building (higher = better quality, slower build)
- Runtime parameter `ef_search` set in queries (typically 100-400 for production)

**Index Creation Migration**:
```python
# alembic/versions/xxx_create_hnsw_index.py

def upgrade():
    op.execute('CREATE EXTENSION IF NOT EXISTS vector')
    op.create_index(
        'ix_face_embeddings_vector_hnsw',
        'face_embeddings',
        ['embedding_vector'],
        postgresql_using='hnsw',
        postgresql_with={'m': 16, 'ef_construction': 200}
    )

def downgrade():
    op.drop_index('ix_face_embeddings_vector_hnsw', table_name='face_embeddings')
```

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system—essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### PBT Applicability Assessment

This system includes several types of operations:
1. **Pure validation logic**: Image size, format, dimensions, filename sanitization
2. **Data transformation**: Response serialization, bounding box calculations, face selection
3. **External integrations**: InsightFace model inference, PostgreSQL queries, file I/O
4. **Infrastructure**: Database connection pooling, pgvector indexes

**Areas suitable for PBT** (our code's logic with meaningful input variation):
- Image validation (size, format, dimensions)
- Filename sanitization and UUID uniqueness
- Response structure validation
- Face selection logic (largest by area)
- Result ordering and limiting

**Areas NOT suitable for PBT** (external services, infrastructure, side effects):
- InsightFace model behavior (external library)
- Database queries and pgvector operations (integration tests)
- File I/O operations (side effects)
- API endpoint routing (integration tests)

### Property Reflection

After analyzing testable properties, I identified these consolidation opportunities:

1. **Image validation properties (10.1, 10.2, 10.3)** can remain separate as they test distinct validation rules
2. **Response structure properties (5.6, 6.7, 8.1-8.7)** can be consolidated into a single comprehensive API response format property
3. **Filename properties (10.4, 10.5)** test different aspects (sanitization vs uniqueness) and should remain separate
4. **Validation error property (10.7)** is redundant with individual validation properties that already verify rejection—remove it
5. **Face selection property (6.8)** and **result ordering property (6.5)** test different algorithms and should remain separate

### Properties

### Property 1: File Size Validation

*For any* file upload, if the file size exceeds 10MB, validation SHALL reject it; if the file size is ≤ 10MB, size validation SHALL pass.

**Validates: Requirements 10.1**

### Property 2: Image Dimension Validation

*For any* image upload, if either dimension exceeds 8000 pixels, validation SHALL reject it; otherwise dimension validation SHALL pass.

**Validates: Requirements 10.2**

### Property 3: Format Header Validation

*For any* file with a JPEG/PNG/WEBP header, format validation SHALL accept it regardless of file extension; for any file without a valid image header, format validation SHALL reject it regardless of file extension.

**Validates: Requirements 10.3, 5.10**

### Property 4: Filename Sanitization

*For any* filename containing directory traversal sequences (../, ..\, absolute paths), the sanitized filename SHALL contain no path separators or directory traversal components.

**Validates: Requirements 10.4**

### Property 5: Filename Uniqueness

*For any* two image uploads processed concurrently or sequentially, the generated filenames SHALL be distinct.

**Validates: Requirements 10.5**

### Property 6: Image Resizing Threshold

*For any* image with width or height exceeding 2048 pixels, the resized image SHALL have both dimensions ≤ 2048 pixels while maintaining aspect ratio; for any image with both dimensions ≤ 2048 pixels, the image SHALL remain unchanged.

**Validates: Requirements 10.6**

### Property 7: Largest Face Selection

*For any* set of detected faces in an image, the selected primary face SHALL have a bounding box area (width × height) greater than or equal to all other detected faces.

**Validates: Requirements 6.8**

### Property 8: Search Results Ordering

*For any* face search result set, the similarity scores SHALL be in descending order (each score ≥ the next score).

**Validates: Requirements 6.5**

### Property 9: Search Results Limit

*For any* face search query, the number of returned results SHALL be ≤ 100, even if more matching faces exist above the threshold.

**Validates: Requirements 6.11**

### Property 10: API Response Structure

*For any* API response (success or error), the JSON body SHALL contain:
- A "success" boolean field
- A "message" string field
- Either a "data" field (success) or "error" field (failure)
- All field names in snake_case

**Validates: Requirements 5.6, 6.7, 8.1, 8.2, 8.3, 8.4, 8.5, 8.6, 8.7**

### Property 11: Confidence Score Extraction

*For any* face detected by InsightFace, the stored confidence_score SHALL equal the det_score value from the InsightFace face object, converted to a Python float.

**Validates: Requirements 4.6**

### Property 12: Invalid Format Rejection

*For any* file that is not a valid JPEG, PNG, or WEBP image (verified by header inspection), the upload SHALL be rejected with a 400 error containing format information.

**Validates: Requirements 5.8**

## Error Handling

### Error Handling Strategy

The system uses a layered error handling approach with custom exceptions and FastAPI exception handlers:

```python
# backend/app/exceptions.py

class AppException(Exception):
    """Base exception for all application errors."""
    def __init__(self, message: str, code: str):
        self.message = message
        self.code = code
        super().__init__(self.message)

class ValidationError(AppException):
    """Raised when input validation fails."""
    def __init__(self, message: str):
        super().__init__(message, "VALIDATION_ERROR")

class EventNotFoundError(AppException):
    """Raised when event_id doesn't exist."""
    def __init__(self, event_id: int):
        super().__init__(f"Event {event_id} not found", "EVENT_NOT_FOUND")

class FaceDetectionError(AppException):
    """Raised when face detection fails."""
    def __init__(self, message: str):
        super().__init__(message, "FACE_DETECTION_ERROR")

class DatabaseError(AppException):
    """Raised when database operations fail."""
    def __init__(self, message: str):
        super().__init__(message, "DATABASE_ERROR")
```

### Exception Handlers

```python
# backend/app/api/exception_handlers.py

from fastapi import Request
from fastapi.responses import JSONResponse
import logging

logger = logging.getLogger(__name__)

@app.exception_handler(ValidationError)
async def validation_error_handler(request: Request, exc: ValidationError):
    logger.warning(f"Validation error: {exc.message}", extra={"request_id": request.state.request_id})
    return JSONResponse(
        status_code=400,
        content={
            "success": False,
            "message": exc.message,
            "error": {"code": exc.code, "details": exc.message}
        }
    )

@app.exception_handler(EventNotFoundError)
async def not_found_error_handler(request: Request, exc: EventNotFoundError):
    logger.info(f"Resource not found: {exc.message}", extra={"request_id": request.state.request_id})
    return JSONResponse(
        status_code=404,
        content={
            "success": False,
            "message": exc.message,
            "error": {"code": exc.code}
        }
    )

@app.exception_handler(DatabaseError)
async def database_error_handler(request: Request, exc: DatabaseError):
    logger.error(f"Database error: {exc.message}", extra={"request_id": request.state.request_id})
    return JSONResponse(
        status_code=503,
        content={
            "success": False,
            "message": "Service temporarily unavailable",
            "error": {"code": "SERVICE_UNAVAILABLE"}
        },
        headers={"Retry-After": "60"}
    )

@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    logger.exception("Unhandled exception", extra={"request_id": request.state.request_id})
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "message": "Internal server error",
            "error": {"code": "INTERNAL_ERROR"}
        }
    )
```

### Error Response Format

All error responses follow this structure:
```json
{
  "success": false,
  "message": "Human-readable error description",
  "error": {
    "code": "ERROR_CODE",
    "details": "Optional additional error information"
  }
}
```

### Logging Strategy

**Structured Logging Configuration**:
```python
# backend/app/logging_config.py

import logging
import sys
from pythonjsonlogger import jsonlogger

def setup_logging():
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    
    handler = logging.StreamHandler(sys.stdout)
    formatter = jsonlogger.JsonFormatter(
        fmt='%(asctime)s %(levelname)s %(name)s %(message)s %(request_id)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)
```

**Request ID Middleware**:
```python
# backend/app/middleware/request_id.py

import uuid
from starlette.middleware.base import BaseHTTPMiddleware

class RequestIDMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        request_id = request.headers.get('X-Request-ID', str(uuid.uuid4()))
        request.state.request_id = request_id
        
        response = await call_next(request)
        response.headers['X-Request-ID'] = request_id
        return response
```

### Face Detection Error Handling

InsightFace failures are caught and logged without rolling back photo records:

```python
# In photo_service.py upload_photo method

try:
    faces = await self.face_service.detect_faces(str(full_path))
    # Process embeddings...
except Exception as e:
    logger.error(
        f"Face detection failed for photo {photo.photo_id}",
        extra={
            "photo_id": photo.photo_id,
            "error": str(e),
            "request_id": request_id
        }
    )
    # Photo record remains, face_embeddings empty
    return {
        'photo_id': photo.photo_id,
        'face_count': 0,
        'file_path': file_path,
        'warning': 'Face detection failed'
    }
```

## Testing Strategy

### Testing Approach

The system uses a dual testing strategy combining property-based tests for validation logic and integration tests for external dependencies:

**1. Property-Based Tests** (using Hypothesis for Python):
- Image validation rules
- Filename sanitization and generation
- Face selection algorithms
- Response structure validation
- Result ordering and limiting

**2. Integration Tests** (using pytest with test database):
- Database CRUD operations
- InsightFace face detection workflow
- File storage operations
- Full API endpoint workflows
- pgvector similarity search

**3. Unit Tests** (using pytest):
- Specific error scenarios
- Edge cases (no faces detected, multiple faces, etc.)
- Configuration validation
- Middleware behavior

### Property-Based Testing Configuration

**Library**: Hypothesis 6.100+

**Test Configuration**:
```python
# backend/tests/property_tests/conftest.py

from hypothesis import settings, HealthCheck

settings.register_profile("ci", max_examples=100, suppress_health_check=[HealthCheck.too_slow])
settings.register_profile("dev", max_examples=20)
settings.load_profile("ci")  # Default to 100 iterations
```

**Test Tagging**:
Each property test includes a comment referencing its design property:
```python
# Feature: ai-wedding-photo-portal, Property 1: File Size Validation
@given(file_size=st.integers(min_value=0, max_value=20*1024*1024))
def test_file_size_validation(file_size):
    """Property 1: Files > 10MB rejected, files ≤ 10MB pass size validation."""
    validator = ImageValidator()
    # ...test implementation
```

### Test Organization

```
backend/tests/
├── property_tests/           # Property-based tests
│   ├── test_image_validation.py
│   ├── test_filename_generation.py
│   ├── test_face_selection.py
│   ├── test_response_structure.py
│   └── test_search_logic.py
├── integration_tests/        # Integration tests
│   ├── test_photo_upload_endpoint.py
│   ├── test_face_search_endpoint.py
│   ├── test_database_operations.py
│   └── test_insightface_integration.py
├── unit_tests/              # Unit tests
│   ├── test_error_handlers.py
│   ├── test_middleware.py
│   └── test_configuration.py
└── fixtures/                # Test data and fixtures
    ├── sample_images/
    └── test_database.py
```

### Example Property-Based Tests

**Image Validation Test**:
```python
# backend/tests/property_tests/test_image_validation.py

from hypothesis import given, strategies as st
import io
from PIL import Image

# Feature: ai-wedding-photo-portal, Property 1: File Size Validation
@given(file_size_mb=st.floats(min_value=0, max_value=20))
async def test_file_size_validation(file_size_mb):
    """Property 1: Files > 10MB rejected, files ≤ 10MB pass."""
    validator = ImageValidator()
    
    # Generate file of specified size
    file_content = b'x' * int(file_size_mb * 1024 * 1024)
    upload_file = UploadFile(filename="test.jpg", file=io.BytesIO(file_content))
    
    if file_size_mb > 10:
        with pytest.raises(ValidationError, match="exceeds 10MB"):
            await validator.validate_and_prepare(upload_file)
    else:
        # Size validation should not raise for this criterion
        # (may fail on other validations like format)
        try:
            await validator.validate_and_prepare(upload_file)
        except ValidationError as e:
            assert "10MB" not in str(e)

# Feature: ai-wedding-photo-portal, Property 3: Format Header Validation
@given(
    format=st.sampled_from(['JPEG', 'PNG', 'WEBP']),
    wrong_extension=st.sampled_from(['.txt', '.pdf', '.exe'])
)
async def test_format_header_validation(format, wrong_extension):
    """Property 3: Valid headers accepted regardless of extension."""
    validator = ImageValidator()
    
    # Create valid image with wrong extension
    img = Image.new('RGB', (100, 100))
    buffer = io.BytesIO()
    img.save(buffer, format=format)
    buffer.seek(0)
    
    upload_file = UploadFile(
        filename=f"test{wrong_extension}",
        file=buffer
    )
    
    # Should validate based on header, not extension
    result = await validator.validate_and_prepare(upload_file)
    assert result['format'] in ['jpeg', 'png', 'webp']
```

**Face Selection Test**:
```python
# backend/tests/property_tests/test_face_selection.py

from hypothesis import given, strategies as st

# Feature: ai-wedding-photo-portal, Property 7: Largest Face Selection
@given(
    faces=st.lists(
        st.fixed_dictionaries({
            'bbox': st.tuples(
                st.floats(min_value=0, max_value=1000),  # x1
                st.floats(min_value=0, max_value=1000),  # y1
                st.floats(min_value=10, max_value=1000), # x2
                st.floats(min_value=10, max_value=1000)  # y2
            )
        }),
        min_size=1,
        max_size=10
    )
)
def test_largest_face_selection(faces):
    """Property 7: Selected face has largest bounding box area."""
    # Calculate areas
    areas = [
        (face['bbox'][2] - face['bbox'][0]) * (face['bbox'][3] - face['bbox'][1])
        for face in faces
    ]
    max_area = max(areas)
    
    # Mock InsightFace face objects
    mock_faces = [
        type('Face', (), {'bbox': face['bbox']})
        for face in faces
    ]
    
    # Select primary face (implementation from endpoint)
    primary_face = max(
        mock_faces,
        key=lambda f: (f.bbox[2] - f.bbox[0]) * (f.bbox[3] - f.bbox[1])
    )
    
    selected_area = (
        (primary_face.bbox[2] - primary_face.bbox[0]) *
        (primary_face.bbox[3] - primary_face.bbox[1])
    )
    
    assert selected_area == max_area
```

### Integration Test Example

```python
# backend/tests/integration_tests/test_photo_upload_endpoint.py

import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_photo_upload_workflow(async_client: AsyncClient, test_event, sample_jpeg):
    """Test complete photo upload workflow with face detection."""
    response = await async_client.post(
        "/api/photos/upload",
        data={"event_id": test_event.event_id},
        files={"file": ("photo.jpg", sample_jpeg, "image/jpeg")}
    )
    
    assert response.status_code == 201
    data = response.json()
    assert data["success"] is True
    assert "photo_id" in data["data"]
    assert "face_count" in data["data"]
    assert data["data"]["face_count"] >= 0

@pytest.mark.asyncio
async def test_event_not_found(async_client: AsyncClient, sample_jpeg):
    """Test 404 error when event_id doesn't exist."""
    response = await async_client.post(
        "/api/photos/upload",
        data={"event_id": 99999},
        files={"file": ("photo.jpg", sample_jpeg, "image/jpeg")}
    )
    
    assert response.status_code == 404
    data = response.json()
    assert data["success"] is False
    assert "not found" in data["message"].lower()
```

### Test Coverage Goals

- **Property-based tests**: 100 iterations per property (minimum)
- **Unit test coverage**: >80% for validation and business logic
- **Integration test coverage**: All API endpoints and database operations
- **End-to-end tests**: Happy path workflows for upload and search

### CI/CD Integration

```yaml
# .github/workflows/test.yml

name: Tests
on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: pgvector/pgvector:pg15
        env:
          POSTGRES_PASSWORD: test
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
    
    steps:
      - uses: actions/checkout@v3
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install -r requirements-dev.txt
      
      - name: Run property-based tests
        run: pytest backend/tests/property_tests/ -v --hypothesis-profile=ci
      
      - name: Run integration tests
        run: pytest backend/tests/integration_tests/ -v
        env:
          DATABASE_URL: postgresql+asyncpg://postgres:test@localhost:5432/test_db
      
      - name: Generate coverage report
        run: pytest --cov=backend --cov-report=xml
      
      - name: Upload coverage
        uses: codecov/codecov-action@v3
```
