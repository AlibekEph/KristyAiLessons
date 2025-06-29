"""Background tasks for lesson processing"""

import logging
from datetime import datetime
from typing import Optional

from ..interfaces.recording import RecordingServiceInterface
from ..interfaces.transcription import TranscriptionServiceInterface
from ..interfaces.ai_processor import AIProcessorInterface, AIProcessingRequest
from ..interfaces.storage import StorageServiceInterface

logger = logging.getLogger(__name__)


async def process_recording(
    lesson_id: str,
    recording_url: str,
    transcription_service: TranscriptionServiceInterface,
    storage_service: StorageServiceInterface
):
    """Process recording and start transcription"""
    
    try:
        logger.info(f"Processing recording for lesson {lesson_id}")
        
        # Get lesson
        lesson = await storage_service.get_lesson(lesson_id)
        if not lesson:
            logger.error(f"Lesson {lesson_id} not found")
            return
        
        # Import settings directly
        from ..config import Settings
        settings = Settings()
        
        # Start transcription
        webhook_url = f"{settings.APP_URL}/webhooks/assemblyai"
        
        if lesson.lesson_type == "chinese":
            # Use multilingual transcription
            transcription_result = await transcription_service.transcribe_multilingual(
                audio_url=recording_url,
                primary_language="ru",
                secondary_languages=["zh"],
                webhook_url=webhook_url,
                metadata={"lesson_id": lesson_id}
            )
        else:
            # Regular transcription
            transcription_result = await transcription_service.transcribe_audio(
                audio_url=recording_url,
                language_code="ru",
                webhook_url=webhook_url,
                metadata={"lesson_id": lesson_id}
            )
        
        # Update lesson with transcription ID
        lesson.transcription_id = transcription_result.id
        await storage_service.save_lesson(lesson)
        
        logger.info(f"Started transcription {transcription_result.id} for lesson {lesson_id}")
        
    except Exception as e:
        logger.error(f"Failed to process recording: {e}")
        # Update lesson status to failed
        lesson = await storage_service.get_lesson(lesson_id)
        if lesson:
            lesson.status = "failed"
            await storage_service.save_lesson(lesson)


async def process_transcript(
    lesson_id: str,
    transcript: str,
    lesson_type: str,
    student_level: Optional[str],
    ai_processor: AIProcessorInterface,
    storage_service: StorageServiceInterface
):
    """Process transcript with AI"""
    
    try:
        logger.info(f"Processing transcript for lesson {lesson_id}")
        
        # Get lesson
        lesson = await storage_service.get_lesson(lesson_id)
        if not lesson:
            logger.error(f"Lesson {lesson_id} not found")
            return
        
        # Process with AI
        request = AIProcessingRequest(
            transcript=transcript,
            lesson_type=lesson_type,
            student_level=student_level,
            lesson_duration=lesson.ended_at.timestamp() - lesson.started_at.timestamp() if lesson.started_at and lesson.ended_at else None,
            metadata={"lesson_id": lesson_id}
        )
        
        materials = await ai_processor.process_lesson(request)
        
        # Save materials
        await storage_service.save_materials(
            lesson_id,
            {
                "original_transcript": materials.original_transcript,
                "corrected_transcript": materials.corrected_transcript,
                "summary": materials.summary,
                "homework": materials.homework,
                "notes": materials.notes,
                "key_vocabulary": materials.key_vocabulary,
            }
        )
        
        # Update lesson
        lesson.materials_id = materials.id
        lesson.status = "completed"
        await storage_service.save_lesson(lesson)
        
        logger.info(f"Completed processing for lesson {lesson_id}")
        
    except Exception as e:
        logger.error(f"Failed to process transcript: {e}")
        # Update lesson status to failed
        try:
            lesson = await storage_service.get_lesson(lesson_id)
            if lesson:
                lesson.status = "failed"
                await storage_service.save_lesson(lesson)
        except Exception as save_error:
            logger.error(f"Failed to update lesson status to failed: {save_error}")


async def process_lesson_with_polling(
    lesson_id: str,
    bot_id: str,
    timeout: int,
    interval: int,
    recording_service: RecordingServiceInterface,
    ai_processor: AIProcessorInterface,
    storage_service: StorageServiceInterface
):
    """Process lesson using direct API polling instead of webhooks"""
    
    try:
        logger.info(f"Starting polling process for lesson {lesson_id}, bot {bot_id}")
        
        # Get lesson
        lesson = await storage_service.get_lesson(lesson_id)
        if not lesson:
            logger.error(f"Lesson {lesson_id} not found during polling")
            return
        
        # Wait for recording and transcript to be ready using polling
        success = await recording_service.poll_until_ready(bot_id, timeout, interval)
        
        if not success:
            logger.error(f"Polling timeout or failed for lesson {lesson_id}, bot {bot_id}")
            lesson.status = "failed"
            await storage_service.save_lesson(lesson)
            return
        
        # Get transcript data
        transcript_data = await recording_service.get_transcript_data(bot_id)
        if not transcript_data:
            logger.error(f"No transcript data available for lesson {lesson_id}, bot {bot_id}")
            lesson.status = "failed"
            await storage_service.save_lesson(lesson)
            return
        
        # Save transcript
        await storage_service.save_transcript(
            lesson_id,
            {
                "text": transcript_data.get("text", ""),
                "segments": transcript_data.get("words", []),
                "language_code": transcript_data.get("language_code", "ru"),
                "duration": transcript_data.get("audio_duration", 0),
            }
        )
        
        # Update lesson with transcript ID
        lesson.transcription_id = transcript_data.get("id")
        lesson.status = "processing"
        await storage_service.save_lesson(lesson)
        
        logger.info(f"Transcript saved for lesson {lesson_id}, starting AI processing")
        
        # Process with AI
        request = AIProcessingRequest(
            transcript=transcript_data.get("text", ""),
            lesson_type=lesson.lesson_type,
            student_level=lesson.lesson_metadata.get("student_level"),
            lesson_duration=None,
            metadata={"lesson_id": lesson_id, "source": "polling"}
        )
        
        materials = await ai_processor.process_lesson(request)
        
        # Save materials
        await storage_service.save_materials(
            lesson_id,
            {
                "original_transcript": materials.original_transcript,
                "corrected_transcript": materials.corrected_transcript,
                "summary": materials.summary,
                "homework": materials.homework,
                "notes": materials.notes,
                "key_vocabulary": materials.key_vocabulary,
            }
        )
        
        # Update lesson
        lesson.materials_id = materials.id
        lesson.status = "completed"
        lesson.ended_at = datetime.now()
        await storage_service.save_lesson(lesson)
        
        logger.info(f"Successfully completed polling processing for lesson {lesson_id}")
        
    except Exception as e:
        logger.error(f"Failed to process lesson {lesson_id} with polling: {e}")
        
        # Update lesson status to failed
        try:
            lesson = await storage_service.get_lesson(lesson_id)
            if lesson:
                lesson.status = "failed"
                await storage_service.save_lesson(lesson)
        except Exception as save_error:
            logger.error(f"Failed to update lesson status to failed: {save_error}") 