"""Interfaces for replaceable components"""

from .recording import RecordingServiceInterface
from .transcription import TranscriptionServiceInterface
from .ai_processor import AIProcessorInterface
from .storage import StorageServiceInterface

__all__ = [
    'RecordingServiceInterface',
    'TranscriptionServiceInterface',
    'AIProcessorInterface',
    'StorageServiceInterface'
] 