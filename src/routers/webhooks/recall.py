"""API endpoint to handle Recall.ai webhooks."""

import asyncio
import logging
from datetime import datetime
from typing import Dict, Any, Optional
from fastapi import APIRouter, Depends, BackgroundTasks

from ...dependencies import (
    get_recording_service,
    get_transcription_service,
    get_storage_service
)
from ...interfaces.recording import RecordingServiceInterface
from ...interfaces.transcription import TranscriptionServiceInterface
from ...interfaces.storage import StorageServiceInterface, Lesson
from ...services.enhanced_transcription_service import EnhancedTranscriptionService
from ...config import Settings
from ...utils.webhook_logger import log_webhook_event, log_webhook_error

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post(
    "/recall",
    summary="Webhook для Recall.ai",
    description="""
    Обрабатывает уведомления от Recall.ai о статусе записи.
    
    Поддерживаемые события:
    - bot.joining_call - бот подключается к звонку
    - bot.in_waiting_room - бот в комнате ожидания
    - bot.in_call_not_recording - бот в звонке, но не записывает
    - bot.recording_permission_allowed - разрешение на запись получено
    - bot.recording_permission_denied - разрешение на запись отклонено
    - bot.in_call_recording - бот записывает
    - bot.call_ended - звонок завершен
    - bot.done - бот завершил работу (запись готова)
    - bot.fatal - критическая ошибка бота
    """,
    include_in_schema=False
)
async def handle_recall_webhook(
    webhook_data: Dict[str, Any],
    background_tasks: BackgroundTasks,
    recording_service: RecordingServiceInterface = Depends(get_recording_service),
    transcription_service: TranscriptionServiceInterface = Depends(get_transcription_service),
    storage_service: StorageServiceInterface = Depends(get_storage_service)
):
    """Обработка webhooks от Recall.ai"""

    event_type = webhook_data.get("event")
    processing_result = {
        "status_changed": False,
        "timestamps_updated": [],
        "background_processing_started": False,
        "lesson_id": None,
        "old_status": None,
        "new_status": None
    }

    try:
        # Извлекаем данные из webhook'а
        bot_data = webhook_data.get("data", {}).get("bot", {})
        bot_id = bot_data.get("id")
        
        status_data = webhook_data.get("data", {}).get("data", {})
        status_code = status_data.get("code")
        updated_at_str = status_data.get("updated_at")

        logger.info(f"Received Recall webhook: {event_type} for bot {bot_id}, status: {status_code}")

        if not bot_id:
            processing_result["error"] = "No bot_id found"
            await log_webhook_event("recall", event_type or "unknown", webhook_data, processing_result)
            return {"status": "ok", "message": "No bot_id found"}

        # Найти урок по bot_id
        lesson = await _find_lesson_by_bot_id(storage_service, bot_id)
        if not lesson:
            processing_result["error"] = "Lesson not found"
            await log_webhook_event("recall", event_type, webhook_data, processing_result)
            return {"status": "ok", "message": "Lesson not found"}

        processing_result["lesson_id"] = str(lesson.id)
        processing_result["old_status"] = lesson.status

        # Обновить статус урока на основе события
        update_result = await _update_lesson_from_webhook(lesson, event_type, status_code, updated_at_str, storage_service)
        processing_result.update(update_result)

        # Запустить фоновую обработку для завершенных записей
        if event_type in ["bot.done"]:
            bg_result = await _start_enhanced_transcription_processing(
                lesson, bot_id, background_tasks, recording_service, storage_service
            )
            processing_result["background_processing_started"] = bg_result

        # Логируем успешную обработку
        await log_webhook_event("recall", event_type, webhook_data, processing_result)
        
        return {"status": "ok"}

    except Exception as e:
        logger.error(f"Failed to handle Recall webhook: {e}")
        processing_result["error"] = str(e)
        
        # Логируем ошибку
        log_webhook_error("recall", event_type or "unknown", e, webhook_data)
        await log_webhook_event("recall", event_type or "unknown", webhook_data, processing_result)
        
        return {"status": "error", "message": str(e)} 


async def _find_lesson_by_bot_id(storage_service: StorageServiceInterface, bot_id: str) -> Optional[Lesson]:
    """Найти урок по bot_id"""
    lessons = await storage_service.list_lessons()
    # Ищем по recall_bot_id, затем по recording_session_id для обратной совместимости
    return next((l for l in lessons if l.recall_bot_id == bot_id or l.recording_session_id == bot_id), None)


async def _update_lesson_from_webhook(
    lesson: Lesson, 
    event_type: str, 
    status_code: str, 
    updated_at_str: str,
    storage_service: StorageServiceInterface
) -> Dict[str, Any]:
    """Обновить статус урока на основе webhook события"""
    
    result = {
        "status_changed": False,
        "new_status": lesson.status,
        "timestamps_updated": []
    }
    
    # Маппинг событий Recall к статусам урока
    event_to_status_mapping = {
        "bot.joining_call": "recording",
        "bot.in_waiting_room": "recording",
        "bot.in_call_not_recording": "recording", 
        "bot.recording_permission_allowed": "recording",
        "bot.recording_permission_denied": "failed",
        "bot.in_call_recording": "recording",
        "bot.call_ended": "transcribing",
        "bot.done": "transcribing",  # Изменил на transcribing вместо completed
        "bot.fatal": "failed"
    }
    
    # Обновляем статус урока
    new_status = event_to_status_mapping.get(event_type)
    if new_status and new_status != lesson.status:
        old_status = lesson.status
        lesson.status = new_status
        result["status_changed"] = True
        result["new_status"] = new_status
        logger.info(f"Updated lesson {lesson.id} status from '{old_status}' to '{new_status}' via webhook {event_type}")
    
    # Обновляем временные метки на основе события
    if updated_at_str:
        try:
            updated_at = datetime.fromisoformat(updated_at_str.replace('Z', '+00:00'))
            
            # Устанавливаем started_at при начале записи
            if event_type == "bot.in_call_recording" and not lesson.started_at:
                lesson.started_at = updated_at
                result["timestamps_updated"].append(f"started_at = {updated_at}")
                logger.info(f"Set lesson {lesson.id} started_at to {updated_at}")
            
            # Устанавливаем ended_at при завершении звонка
            if event_type in ["bot.call_ended", "bot.done"] and not lesson.ended_at:
                lesson.ended_at = updated_at
                result["timestamps_updated"].append(f"ended_at = {updated_at}")
                logger.info(f"Set lesson {lesson.id} ended_at to {updated_at}")
                
        except ValueError as e:
            logger.warning(f"Failed to parse updated_at timestamp '{updated_at_str}': {e}")
            result["timestamp_parse_error"] = str(e)
    
    # Сохраняем изменения
    await storage_service.save_lesson(lesson)
    
    return result


async def _start_enhanced_transcription_processing(
    lesson: Lesson,
    bot_id: str,
    background_tasks: BackgroundTasks,
    recording_service: RecordingServiceInterface,
    storage_service: StorageServiceInterface
) -> bool:
    """Запустить улучшенную обработку транскрипции для завершенной записи"""
    
    try:
        # Получаем данные о записи
        recording_session = await recording_service.get_recording_status(bot_id)
        
        if not recording_session.recording_url:
            logger.warning(f"No recording URL found for lesson {lesson.id}, bot {bot_id}")
            return False
        
        # Получаем recording_id из bot_data
        recording_id = None
        try:
            bot_data = await recording_service.get_bot_data(bot_id)
            if bot_data and 'recordings' in bot_data and bot_data['recordings']:
                # recording_id находится в recordings[0]["id"]
                recording_id = bot_data['recordings'][0]['id']
        except Exception as e:
            logger.warning(f"Could not get recording_id for lesson {lesson.id}: {e}")
        
        if not recording_id:
            logger.warning(f"No recording_id found for lesson {lesson.id}, bot {bot_id}")
            return False
        
        # Обновляем урок с recording_id
        lesson.recording_id = recording_id
        await storage_service.save_lesson(lesson)
        
        logger.info(f"Starting enhanced transcription processing for lesson {lesson.id}, recording_id: {recording_id}")
        
        # Запускаем фоновую задачу с улучшенной транскрипцией
        background_tasks.add_task(
            _process_enhanced_transcription,
            str(lesson.id),
            recording_id,
            lesson.lesson_type,
            storage_service
        )
        return True
            
    except Exception as e:
        logger.error(f"Failed to start enhanced transcription processing for lesson {lesson.id}: {e}")
        return False


async def _process_enhanced_transcription(
    lesson_id: str,
    recording_id: str,
    lesson_type: str,
    storage_service: StorageServiceInterface
):
    """Фоновая задача для обработки транскрипции с помощью EnhancedTranscriptionService"""
    
    try:
        logger.info(f"Processing enhanced transcription for lesson {lesson_id}, recording_id: {recording_id}")
        
        # Получаем настройки
        settings = Settings()
        
        # Создаем экземпляр улучшенного сервиса транскрипции
        enhanced_service = EnhancedTranscriptionService(
            recall_api_key=settings.RECALL_API_KEY,
            assemblyai_api_key=settings.ASSEMBLYAI_API_KEY
        )
        
        # Определяем тип урока для передачи в сервис
        service_lesson_type = "chinese" if lesson_type in ["chinese", "китайский"] else "english"
        
        # Запускаем транскрипцию
        result = await enhanced_service.transcribe_lesson(
            recording_id=recording_id,
            lesson_type=service_lesson_type,
            use_multiple_approaches=True
        )
        
        if not result or not result.get("best_result"):
            logger.error(f"Enhanced transcription failed for lesson {lesson_id}")
            await _update_lesson_status(lesson_id, "failed", storage_service)
            return
        
        best_result = result["best_result"]
        transcript_text = best_result.get("text", "")
        language_info = best_result.get("language_analysis", {})
        
        # Создаем уникальный transcript_id
        import uuid
        transcript_id = str(uuid.uuid4())
        
        # Сохраняем транскрипцию в базе данных
        await storage_service.save_transcript(
            lesson_id,
            {
                "id": transcript_id,
                "text": transcript_text,
                "language_code": language_info.get("detected_language", "ru"),
                "duration": best_result.get("audio_duration", 0),
                "segments": best_result.get("words", []),
                "transcript_metadata": {
                    "method": "enhanced_transcription",
                    "confidence": best_result.get("confidence", 0.0),
                    "language_analysis": language_info,
                    "approach_used": result.get("approach_used", "unknown")
                }
            }
        )
        
        # Обновляем урок
        lesson = await storage_service.get_lesson(lesson_id)
        if lesson:
            lesson.transcript_id = transcript_id
            lesson.status = "completed"
            await storage_service.save_lesson(lesson)
        
        logger.info(f"Enhanced transcription completed successfully for lesson {lesson_id}")
        
    except Exception as e:
        logger.error(f"Failed to process enhanced transcription for lesson {lesson_id}: {e}")
        await _update_lesson_status(lesson_id, "failed", storage_service)


async def _update_lesson_status(lesson_id: str, status: str, storage_service: StorageServiceInterface):
    """Обновить статус урока"""
    try:
        lesson = await storage_service.get_lesson(lesson_id)
        if lesson:
            lesson.status = status
            await storage_service.save_lesson(lesson)
    except Exception as e:
        logger.error(f"Failed to update lesson {lesson_id} status to {status}: {e}") 