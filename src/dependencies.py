"""Dependency injection for FastAPI"""

from functools import lru_cache
from .config import settings
from .interfaces.recording import RecordingServiceInterface
from .interfaces.transcription import TranscriptionServiceInterface
from .interfaces.ai_processor import AIProcessorInterface
from .interfaces.storage import StorageServiceInterface

# Import implementations
from .services.recall_service import RecallService
from .services.assemblyai_service import AssemblyAIService
from .services.yandexgpt_service import YandexGPTService
from .services.local_storage import LocalStorageService
from .utils.api_logger import get_api_logs


@lru_cache()
def get_recording_service() -> RecordingServiceInterface:
    """Get recording service instance"""
    return RecallService(
        api_key=settings.RECALL_API_KEY,
        base_url=f"https://{settings.RECALL_REGION}.recall.ai/api/v1"
    )


@lru_cache()
def get_transcription_service() -> TranscriptionServiceInterface:
    """Get transcription service instance"""
    return AssemblyAIService(api_key=settings.ASSEMBLYAI_API_KEY)


@lru_cache()
def get_ai_processor() -> AIProcessorInterface:
    """Get AI processor instance"""
    return YandexGPTService(
        folder_id=settings.YANDEX_FOLDER_ID,
        api_key=settings.YANDEX_API_KEY,
        model_uri=settings.YANDEX_MODEL_URI
    )


@lru_cache()
def get_storage_service() -> StorageServiceInterface:
    """Get storage service instance"""
    if settings.STORAGE_TYPE == "local":
        return LocalStorageService(storage_path=settings.STORAGE_PATH)
    else:
        raise ValueError(f"Unsupported storage type: {settings.STORAGE_TYPE}") 