"""API endpoint to handle AssemblyAI webhooks."""

import logging
from typing import Dict, Any
from fastapi import APIRouter, Depends, BackgroundTasks

from ...dependencies import (
    get_transcription_service,
    get_ai_processor,
    get_storage_service
)
from ...interfaces.transcription import TranscriptionServiceInterface
from ...interfaces.ai_processor import AIProcessorInterface
from ...interfaces.storage import StorageServiceInterface
from ..background_tasks import process_transcript

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post(
    "/assemblyai",
    summary="Webhook для AssemblyAI",
    description="Обрабатывает уведомления от AssemblyAI о готовности транскрипции",
    include_in_schema=False
)
async def handle_assemblyai_webhook(
    webhook_data: Dict[str, Any],
    background_tasks: BackgroundTasks,
    transcription_service: TranscriptionServiceInterface = Depends(get_transcription_service),
    ai_processor: AIProcessorInterface = Depends(get_ai_processor),
    storage_service: StorageServiceInterface = Depends(get_storage_service)
):
    """Обработка webhooks от AssemblyAI"""

    try:
        transcript_id = webhook_data.get("transcript_id")
        status = webhook_data.get("status")

        logger.info(f"Received AssemblyAI webhook: {status} for transcript {transcript_id}")

        if status == "completed" and transcript_id:
            lessons = await storage_service.list_lessons()
            # Convert transcript_id to string for comparison since it's stored as string in transcription_id
            lesson = next((l for l in lessons if str(l.transcription_id) == transcript_id), None)

            if lesson:
                logger.info(f"Found lesson {lesson.id} for transcript {transcript_id}")
                transcription_result = await transcription_service.get_transcription_result(transcript_id)
                await storage_service.save_transcript(
                    str(lesson.id),
                    {
                        "text": transcription_result.text,
                        "segments": [
                            {
                                "text": seg.text,
                                "start": seg.start,
                                "end": seg.end,
                                "speaker": seg.speaker
                            }
                            for seg in transcription_result.segments
                        ],
                        "language_code": transcription_result.language_code,
                        "duration": transcription_result.duration
                    }
                )

                lesson.status = "processing"
                await storage_service.save_lesson(lesson)
                logger.info(f"Updated lesson {lesson.id} status to processing")

                background_tasks.add_task(
                    process_transcript,
                    str(lesson.id),
                    transcription_result.text,
                    lesson.lesson_type,
                    lesson.lesson_metadata.get("student_level") if lesson.lesson_metadata else None,
                    ai_processor,
                    storage_service
                )
                logger.info(f"Started AI processing for lesson {lesson.id}")
            else:
                logger.warning(f"No lesson found for transcript {transcript_id}")

        return {"status": "ok"}

    except Exception as e:
        logger.error(f"Failed to handle AssemblyAI webhook: {e}")
        return {"status": "error", "message": str(e)} 