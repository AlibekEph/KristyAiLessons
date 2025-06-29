"""API endpoint to get the transcript of a lesson."""

import uuid
import aiohttp
from fastapi import APIRouter, HTTPException, Depends, Path
from typing import Dict, Any

from ...dependencies import get_storage_service, get_db
from ...interfaces.storage import StorageServiceInterface
from ...config import get_settings
from sqlalchemy import text

router = APIRouter()

@router.get(
    "/{lesson_id}/transcript",
    summary="Получить транскрипцию урока",
    description="""
    Возвращает полную транскрипцию урока с временными метками и распознанными спикерами.

    Транскрипция включает:
    - Полный текст урока
    - Сегменты с временными метками
    - Информацию о спикерах
    - Язык транскрипции
    """,
    responses={
        200: {
            "description": "Транскрипция урока",
            "content": {
                "application/json": {
                    "example": {
                        "id": "transcript_123",
                        "text": "Преподаватель: Привет! Сегодня мы изучаем числа. На китайском один будет 一 (yī)...",
                        "segments": [
                            {
                                "text": "Привет! Сегодня мы изучаем числа.",
                                "start": 0.0,
                                "end": 3.5,
                                "speaker": "Teacher"
                            }
                        ],
                        "language": "ru",
                        "duration": 1800.0
                    }
                }
            }
        },
        404: {"description": "Урок или транскрипция не найдены"}
    }
)
async def get_transcript(
    lesson_id: uuid.UUID = Path(..., description="ID урока"),
    storage_service: StorageServiceInterface = Depends(get_storage_service)
):
    """Получить транскрипцию урока"""

    lesson = await storage_service.get_lesson(str(lesson_id))
    if not lesson:
        raise HTTPException(status_code=404, detail="Lesson not found")
    
    # Get transcript_id via direct database query
    transcript_id = None
    try:
        db = storage_service.db
        result = db.execute(
            text("SELECT transcript_id FROM lessons WHERE id = :lesson_id"),
            {"lesson_id": str(lesson_id)}
        )
        row = result.fetchone()
        if row and row[0]:
            transcript_id = str(row[0])
    except Exception as e:
        print(f"Error getting transcript_id: {e}")
    
    if not transcript_id:
        raise HTTPException(status_code=404, detail="Transcript not found")

    # Try to get from local storage first
    transcript_data = await storage_service.get_json(f"transcript_{lesson_id}")
    if transcript_data:
        return transcript_data

    # If not in local storage, fetch from Recall API with post-processing
    settings = get_settings()
    
    # Try to get enhanced transcript with post-processing
    from ...services.multilingual_transcription_service import MultilingualTranscriptionService
    multilingual_service = MultilingualTranscriptionService(settings.RECALL_API_KEY)
    
    transcript_data = await multilingual_service.get_transcript_with_post_processing(transcript_id)
    
    if not transcript_data:
        # Fallback to basic fetch
        transcript_data = await _fetch_transcript_from_recall(transcript_id, settings.RECALL_API_KEY)

    if not transcript_data:
        raise HTTPException(status_code=404, detail="Transcript not found")

    # Save to local storage for future requests
    await storage_service.save_json(f"transcript_{lesson_id}", transcript_data)
    
    return transcript_data


async def _fetch_transcript_from_recall(transcript_id: str, api_key: str) -> Dict[str, Any]:
    """Fetch transcript data from Recall API"""
    
    headers = {
        "Authorization": f"Token {api_key}",
        "Content-Type": "application/json"
    }
    
    async with aiohttp.ClientSession() as session:
        try:
            # Get transcript metadata
            async with session.get(
                f"https://us-west-2.recall.ai/api/v1/transcript/{transcript_id}",
                headers=headers
            ) as response:
                if response.status != 200:
                    return None
                
                transcript_meta = await response.json()
                
                # Check if transcript is ready
                if transcript_meta.get("status", {}).get("code") != "done":
                    return None
                
                # Get download URL
                download_url = transcript_meta.get("data", {}).get("download_url")
                if not download_url:
                    return None
                
                # Download transcript data
                async with session.get(download_url) as download_response:
                    if download_response.status != 200:
                        return None
                    
                    return await download_response.json()
                    
        except Exception as e:
            print(f"Error fetching transcript from Recall: {e}")
            return None 