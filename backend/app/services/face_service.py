"""
Face recognition service using InsightFace.

This module provides face detection and embedding generation using the
InsightFace library.  The model pack and quality thresholds are configurable
through application settings; ``buffalo_s`` remains the default so existing
stored embeddings remain compatible.
"""

import asyncio
import logging
import threading
from typing import List, Optional, Tuple
import numpy as np
from PIL import Image, ImageOps

from app.config import get_settings
from app.exceptions import FaceDetectionError


class FaceInfo:
    """
    Container for face detection information.
    
    Attributes:
        bbox: Bounding box as (x1, y1, x2, y2)
        embedding: 512-dimensional face embedding vector
        confidence: Detection confidence score (0.0 to 1.0)
    """
    
    def __init__(
        self,
        bbox: Tuple[float, float, float, float],
        embedding: np.ndarray,
        confidence: float
    ):
        """
        Initialize face information.
        
        Args:
            bbox: Bounding box coordinates (x1, y1, x2, y2)
            embedding: Face embedding vector
            confidence: Detection confidence score
        """
        self.bbox = bbox
        self.embedding = embedding
        self.confidence = confidence
    
    def to_dict(self) -> dict:
        """
        Convert face info to dictionary format.
        
        Returns:
            Dictionary with bbox, embedding, and confidence
        """
        return {
            "bbox": {
                "x1": float(self.bbox[0]),
                "y1": float(self.bbox[1]),
                "x2": float(self.bbox[2]),
                "y2": float(self.bbox[3])
            },
            "embedding": self.embedding.tolist(),
            "confidence": float(self.confidence)
        }
    
    def bbox_as_dict(self) -> dict:
        """
        Get bounding box as dictionary.
        
        Returns:
            Dictionary with x1, y1, x2, y2
        """
        return {
            "x1": float(self.bbox[0]),
            "y1": float(self.bbox[1]),
            "x2": float(self.bbox[2]),
            "y2": float(self.bbox[3])
        }
    
    def bbox_area(self) -> float:
        """
        Calculate bounding box area.
        
        Returns:
            Area in pixels
        """
        return (self.bbox[2] - self.bbox[0]) * (self.bbox[3] - self.bbox[1])


class FaceRecognitionService:
    """
    Service for face detection and embedding generation using InsightFace.
    
    Uses the configured InsightFace model which provides:
    - SCRFD face detection
    - 512-dimensional embeddings
    - Good performance on diverse faces
    """
    
    def __init__(
        self,
        model_name: Optional[str] = None,
        detection_size: Optional[int] = None,
        min_confidence: Optional[float] = None,
        min_face_size: Optional[int] = None,
    ):
        """
        Initialize the face recognition service.
        
        Loads the configured InsightFace model with the CPU provider.
        This may take a few seconds on first initialization.
        """
        self.logger = logging.getLogger(__name__)
        settings = get_settings()
        self.model_name = (model_name or settings.INSIGHTFACE_MODEL).strip().lower()
        self.detection_size = detection_size or settings.FACE_DETECTION_SIZE
        self.min_confidence = (
            settings.FACE_MIN_DETECTION_CONFIDENCE
            if min_confidence is None else min_confidence
        )
        self.min_face_size = min_face_size or settings.FACE_MIN_SIZE
        self.logger.info(
            "Initializing FaceRecognitionService",
            extra={
                "model": self.model_name,
                "detection_size": self.detection_size,
                "min_confidence": self.min_confidence,
                "min_face_size": self.min_face_size,
            },
        )

        try:
            # Lazy import: insightface pulls in cv2/onnxruntime which require
            # X11 libs (libxcb) that aren't present in minimal runtimes.
            # Importing here (instead of at module level) allows the app to
            # start even if face recognition is never used.
            from insightface.app import FaceAnalysis

            self.app = FaceAnalysis(
                name=self.model_name,
                providers=['CPUExecutionProvider']  # Use CPU for compatibility
            )
            
            # Prepare the model with detection size 640x640
            # This is a good balance between speed and accuracy
            # ctx_id=-1 explicitly selects CPU.  Passing 0 while only a CPU
            # provider is configured is version-dependent and can make
            # InsightFace attempt an unavailable CUDA context.
            self.app.prepare(
                ctx_id=-1,
                det_thresh=self.min_confidence,
                det_size=(self.detection_size, self.detection_size),
            )
            
            self.logger.info("FaceRecognitionService initialized successfully")
            
        except Exception as e:
            self.logger.error(
                f"Failed to initialize FaceRecognitionService: {str(e)}",
                exc_info=True
            )
            raise FaceDetectionError(f"Failed to initialize face recognition: {str(e)}")
    
    async def detect_faces(self, image: Image.Image) -> List[FaceInfo]:
        """
        Detect faces in an image and extract embeddings.
        
        Args:
            image: PIL Image object
            
        Returns:
            List of FaceInfo objects, one per detected face
            
        Raises:
            FaceDetectionError: If face detection fails
        """
        try:
            if not isinstance(image, Image.Image):
                raise FaceDetectionError("Face detection requires a PIL image")

            # Lazy import: cv2 requires X11 libs (libxcb) that aren't present
            # in minimal runtimes, so it's imported here rather than at
            # module level.
            import cv2

            # Normalize EXIF orientation and image mode before inference.  A
            # phone selfie is commonly stored as a rotated JPEG, and RGB-only
            # conversion avoids failures on grayscale/RGBA uploads.
            prepared_image = ImageOps.exif_transpose(image).convert("RGB")
            img_array = np.ascontiguousarray(np.asarray(prepared_image, dtype=np.uint8))
            
            # Convert RGB to BGR for OpenCV/InsightFace
            img_bgr = cv2.cvtColor(img_array, cv2.COLOR_RGB2BGR)
            
            # Detect faces. This is CPU-bound ONNX inference; run it off the
            # event loop thread so it doesn't block other requests while
            # face processing runs in-process (no separate worker anymore).
            faces = await asyncio.to_thread(self.app.get, img_bgr)
            
            self.logger.info(
                f"Detected {len(faces)} face(s) in image",
                extra={"num_faces": len(faces)}
            )
            
            # Convert to FaceInfo objects.  InsightFace normally exposes a
            # normalized embedding, but normalize again defensively so all
            # stored vectors have a stable unit length for cosine search.
            face_infos = []
            for face in faces:
                # Extract confidence score
                confidence = float(getattr(face, "det_score", 0.0))
                if not np.isfinite(confidence) or confidence < self.min_confidence:
                    self.logger.debug(
                        "Discarding low-confidence face",
                        extra={"confidence": confidence, "min_confidence": self.min_confidence},
                    )
                    continue

                # Clamp detector coordinates to the prepared image.  This
                # prevents negative/oversized boxes from leaking into the API
                # and makes area-based face selection deterministic.
                bbox = np.asarray(getattr(face, "bbox", []), dtype=np.float32).reshape(-1)
                if bbox.size != 4 or not np.all(np.isfinite(bbox)):
                    self.logger.warning("Discarding face with invalid bounding box")
                    continue
                height, width = img_array.shape[:2]
                x1, y1, x2, y2 = bbox.tolist()
                x1 = max(0.0, min(float(width), x1))
                y1 = max(0.0, min(float(height), y1))
                x2 = max(0.0, min(float(width), x2))
                y2 = max(0.0, min(float(height), y2))
                if x2 - x1 < self.min_face_size or y2 - y1 < self.min_face_size:
                    self.logger.debug(
                        "Discarding face below minimum size",
                        extra={
                            "width": x2 - x1,
                            "height": y2 - y1,
                            "min_face_size": self.min_face_size,
                        },
                    )
                    continue

                embedding = getattr(face, "normed_embedding", None)
                if embedding is None:
                    embedding = getattr(face, "embedding", None)
                if embedding is None:
                    self.logger.warning("Discarding face without an embedding")
                    continue
                embedding = np.asarray(embedding, dtype=np.float32).reshape(-1)
                if embedding.size != 512 or not np.all(np.isfinite(embedding)):
                    self.logger.warning(
                        "Discarding face with invalid embedding",
                        extra={"embedding_dimensions": int(embedding.size)},
                    )
                    continue
                norm = float(np.linalg.norm(embedding))
                if norm <= 1e-8:
                    self.logger.warning("Discarding face with zero-length embedding")
                    continue
                embedding = embedding / norm

                face_info = FaceInfo(
                    bbox=(x1, y1, x2, y2),
                    embedding=embedding,
                    confidence=confidence
                )
                face_infos.append(face_info)
            
            return face_infos
            
        except FaceDetectionError:
            raise
        except Exception as e:
            self.logger.error(
                f"Face detection failed: {str(e)}",
                exc_info=True
            )
            # An inference failure is not the same as a valid image with no
            # faces.  Propagate it so uploads can be marked as failed-to-index
            # and searches return a useful server error instead of a misleading
            # "no face" validation message.
            raise FaceDetectionError("Face detection failed while processing the image") from e
    
    def extract_embedding(self, face_info: FaceInfo) -> np.ndarray:
        """
        Extract embedding from a face info object.
        
        This is a convenience method since the embedding is already
        computed during detection.
        
        Args:
            face_info: FaceInfo object from detect_faces()
            
        Returns:
            512-dimensional embedding as numpy array
        """
        return face_info.embedding
    
    def select_largest_face(self, faces: List[FaceInfo]) -> Optional[FaceInfo]:
        """
        Select the face with the largest bounding box area.
        
        Useful for selfie processing where we want the primary face.
        
        Args:
            faces: List of FaceInfo objects
            
        Returns:
            FaceInfo with largest bbox, or None if list is empty
        """
        if not faces:
            return None
        
        return max(
            faces,
            key=lambda f: f.bbox_area() * (0.5 + 0.5 * f.confidence),
        )
    
    def filter_by_confidence(
        self,
        faces: List[FaceInfo],
        min_confidence: float = 0.5
    ) -> List[FaceInfo]:
        """
        Filter faces by minimum confidence score.
        
        Args:
            faces: List of FaceInfo objects
            min_confidence: Minimum confidence threshold (0.0 to 1.0)
            
        Returns:
            Filtered list of FaceInfo objects
        """
        return [f for f in faces if f.confidence >= min_confidence]


# Global singleton instance.  Model initialization is expensive and can be
# triggered concurrently by the first upload and first search request, so
# guard the check-and-create sequence as well as the instance itself.
_face_service: Optional[FaceRecognitionService] = None
_face_service_lock = threading.Lock()


def get_face_service() -> FaceRecognitionService:
    """
    Get or create the global FaceRecognitionService instance.
    
    This ensures the model is loaded only once and reused across requests.
    
    Returns:
        FaceRecognitionService instance
    """
    global _face_service
    
    if _face_service is None:
        with _face_service_lock:
            if _face_service is None:
                _face_service = FaceRecognitionService()
    
    return _face_service
