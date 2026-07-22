"""
Face recognition service using InsightFace.

This module provides face detection and embedding generation using the
InsightFace library with the buffalo_l model for high-quality face recognition.
"""

import asyncio
import logging
from typing import List, Optional, Tuple
import numpy as np
import cv2
from PIL import Image

from insightface.app import FaceAnalysis
from insightface.model_zoo import get_model

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
    
    Uses the buffalo_l model which provides:
    - High-quality face detection
    - 512-dimensional embeddings
    - Good performance on diverse faces
    """
    
    def __init__(self):
        """
        Initialize the face recognition service.
        
        Loads the InsightFace buffalo_l model with CPU provider.
        This may take a few seconds on first initialization.
        """
        self.logger = logging.getLogger(__name__)
        self.logger.info("Initializing FaceRecognitionService with buffalo_l model...")
        
        try:
            # Initialize FaceAnalysis with buffalo_l model
            self.app = FaceAnalysis(
                name='buffalo_l',
                providers=['CPUExecutionProvider']  # Use CPU for compatibility
            )
            
            # Prepare the model with detection size 640x640
            # This is a good balance between speed and accuracy
            self.app.prepare(ctx_id=0, det_size=(640, 640))
            
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
            # Convert PIL Image to numpy array (RGB)
            img_array = np.array(image)
            
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
            
            # Convert to FaceInfo objects
            face_infos = []
            for face in faces:
                # Extract bounding box
                bbox = face.bbox.astype(float)
                bbox_tuple = (bbox[0], bbox[1], bbox[2], bbox[3])
                
                # Extract embedding (512-dimensional)
                embedding = face.normed_embedding
                
                # Extract confidence score
                confidence = float(face.det_score)
                
                face_info = FaceInfo(
                    bbox=bbox_tuple,
                    embedding=embedding,
                    confidence=confidence
                )
                face_infos.append(face_info)
            
            return face_infos
            
        except Exception as e:
            self.logger.error(
                f"Face detection failed: {str(e)}",
                exc_info=True
            )
            # Don't raise exception - allow processing to continue
            # Return empty list instead
            self.logger.warning("Returning empty face list due to detection error")
            return []
    
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
        
        return max(faces, key=lambda f: f.bbox_area())
    
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


# Global singleton instance
_face_service: Optional[FaceRecognitionService] = None


def get_face_service() -> FaceRecognitionService:
    """
    Get or create the global FaceRecognitionService instance.
    
    This ensures the model is loaded only once and reused across requests.
    
    Returns:
        FaceRecognitionService instance
    """
    global _face_service
    
    if _face_service is None:
        _face_service = FaceRecognitionService()
    
    return _face_service
