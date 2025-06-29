"""API endpoint to start recording a lesson."""

import logging
from datetime import datetime
import uuid
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks

from ...dependencies import get_recording_service, get_storage_service
from ...interfaces.recording import RecordingServiceInterface
from ...interfaces.storage import StorageServiceInterface, Lesson
from .models import RecordLessonRequest, LessonResponse
from ...schemas import LessonCreate

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post(
    "/record",
    response_model=LessonResponse,
    summary="Начать запись урока",
    description="""
    Запускает процесс записи онлайн-урока.

    После вызова этого эндпоинта:
    1. Recall.ai бот присоединится к встрече
    2. Начнётся запись аудио/видео
    3. После окончания урока автоматически запустится транскрипция
    4. AI обработает транскрипцию и создаст учебные материалы
    """,
    responses={
        200: {
            "description": "Запись успешно начата",
            "content": {
                "application/json": {
                    "example": {
                        "id": "lesson_1234567890.123",
                        "status": "recording",
                        "meeting_url": "https://zoom.us/j/1234567890",
                        "lesson_type": "chinese",
                        "created_at": "2024-01-20T10:30:00",
                        "transcript_available": False,
                        "materials_available": False
                    }
                }
            }
        },
        500: {"description": "Ошибка при запуске записи"}
    }
)
async def start_recording(
    request: RecordLessonRequest,
    background_tasks: BackgroundTasks,
    recording_service: RecordingServiceInterface = Depends(get_recording_service),
    storage_service: StorageServiceInterface = Depends(get_storage_service)
):
    """Start recording a lesson"""

    try:
        # Create lesson record
        lesson_data = LessonCreate(
            meeting_url=request.meeting_url,
            lesson_type=request.lesson_type,
            student_id=request.student_id,
            teacher_id=request.teacher_id,
            status="recording",
            lesson_metadata=request.metadata or {}
        )
        # Convert LessonCreate to Lesson for save_lesson
        lesson = Lesson(**lesson_data.dict(), id=uuid.uuid4(), created_at=datetime.utcnow())
        lesson = await storage_service.save_lesson(lesson)

        # Start recording
        recording_session = await recording_service.start_recording(
            meeting_url=request.meeting_url,
            webhook_url=None,  # Bot status webhooks are configured via Recall Dashboard, not API
            metadata={
                "lesson_id": str(lesson.id),
                "lesson_type": request.lesson_type,
                "student_level": request.student_level
            }
        )

        # Update lesson with Recall bot ID
        lesson.recall_bot_id = recording_session.id
        lesson.recording_session_id = recording_session.id  # Keep for backward compatibility
        await storage_service.save_lesson(lesson)

        logger.info(f"Started recording for lesson {lesson.id}")

        return lesson

    except Exception as e:
        logger.error(f"Failed to start recording: {e}")
        raise HTTPException(status_code=500, detail=str(e)) 