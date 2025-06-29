"""API endpoint to check lesson recording status."""

import logging
from datetime import datetime
from fastapi import APIRouter, HTTPException, Depends

from ...dependencies import get_recording_service, get_storage_service
from ...interfaces.recording import RecordingServiceInterface, RecordingStatus
from ...interfaces.storage import StorageServiceInterface
from .models import ProcessLessonRequest, LessonResponse

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post(
    "/process",
    response_model=LessonResponse,
    summary="Проверить статус записи урока",
    description="""
    Проверяет текущий статус записи урока через прямой запрос к Recall.ai API.

    Процесс проверки:
    1. **Получение урока** - находит урок по ID
    2. **Проверка статуса записи** - делает запрос к API записи
    3. **Обновление информации** - синхронизирует статус урока с состоянием записи

    **Возможные статусы записи:**
    - `pending` - запись еще не началась
    - `recording` - идет процесс записи
    - `completed` - запись завершена и готова к обработке
    - `failed` - ошибка при записи

    **Преимущества:**
    - Мгновенная проверка статуса
    - Не требует ожидания
    - Можно вызывать в любое время
    """,
    responses={
        200: {
            "description": "Статус урока получен",
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
        404: {"description": "Урок не найден"},
        400: {"description": "Отсутствует ID сессии записи"},
        500: {"description": "Ошибка при проверке статуса"}
    }
)
async def process_lesson(
    request: ProcessLessonRequest,
    recording_service: RecordingServiceInterface = Depends(get_recording_service),
    storage_service: StorageServiceInterface = Depends(get_storage_service)
):
    """Проверить статус записи урока"""

    try:
        # Получаем урок
        lesson = await storage_service.get_lesson(str(request.lesson_id))
        if not lesson:
            raise HTTPException(status_code=404, detail="Lesson not found")

        # Use recall_bot_id if available, fallback to recording_session_id for backward compatibility
        bot_id = lesson.recall_bot_id or lesson.recording_session_id
        if not bot_id:
            raise HTTPException(status_code=400, detail="No Recall bot ID found for this lesson")

        logger.info(f"Checking recording status for lesson {request.lesson_id}, bot {bot_id}")

        # Получаем статус записи
        recording_session = await recording_service.get_recording_status(bot_id)
        
        # Обновляем статус урока на основе последнего статуса из status_changes
        new_status = lesson.status  # по умолчанию не меняем статус
        
        if recording_session.status_changes:
            # Получаем последний статус из status_changes
            latest_status_change = recording_session.status_changes[-1]
            latest_status_code = latest_status_change.get("code", "")
            
            # Маппинг статусов Recall к статусам урока
            recall_status_mapping = {
                "joining_call": "recording",
                "in_waiting_room": "recording", 
                "in_call_not_recording": "recording",
                "in_call_recording": "recording",
                "call_ended": "transcribing",
                "recording_done": "transcribing", 
                "done": "completed",
                "fatal": "failed"
            }
            
            new_status = recall_status_mapping.get(latest_status_code, lesson.status)
            
            logger.info(f"Updated lesson {request.lesson_id} status from '{lesson.status}' to '{new_status}' based on Recall status '{latest_status_code}'")
        
        # Обновляем данные урока
        if new_status != lesson.status:
            lesson.status = new_status
        
        # Обновляем started_at на основе status_changes
        if recording_session.status_changes and not lesson.started_at:
            for status_change in recording_session.status_changes:
                if status_change.get("code") == "in_call_recording":
                    created_at = status_change.get("created_at")
                    if created_at:
                        lesson.started_at = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                        break
        
        # Обновляем ended_at на основе status_changes
        if recording_session.status_changes and not lesson.ended_at:
            for status_change in recording_session.status_changes:
                if status_change.get("code") in ["call_ended", "done"]:
                    created_at = status_change.get("created_at")
                    if created_at:
                        lesson.ended_at = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                        break

        # Сохраняем обновленную информацию
        lesson = await storage_service.save_lesson(lesson)

        # Логируем результат проверки статуса
        if recording_session.status_changes:
            latest_status = recording_session.status_changes[-1].get("code", "unknown")
            logger.info(f"Recording status check completed for lesson {request.lesson_id}. Latest Recall status: '{latest_status}', Lesson status: '{lesson.status}'")
        else:
            logger.info(f"Recording status check completed for lesson {request.lesson_id}. No status changes found. Lesson status: '{lesson.status}'")
        
        return lesson

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to check recording status: {e}")
        raise HTTPException(status_code=500, detail=str(e)) 