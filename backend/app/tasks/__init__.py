"""
Background tasks module.

This module contains FastAPI BackgroundTasks used for asynchronous
processing, such as face detection.
"""

from app.tasks import face_processing

__all__ = ['face_processing']
