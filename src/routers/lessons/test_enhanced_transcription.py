"""Test endpoint for enhanced transcription system."""

import uuid
from fastapi import APIRouter, HTTPException, Depends, Path, Query
from typing import Optional
from datetime import datetime

from ...dependencies import get_recording_service, get_settings
from ...interfaces.recording import RecordingServiceInterface
from ...services.enhanced_transcription_service import EnhancedTranscriptionService
from ...config import Settings
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

@router.post(
    "/{lesson_id}/test-enhanced-transcription",
    summary="Тестировать улучшенную транскрипцию",
    description="""
    Тестовый endpoint для проверки новой системы мультиязычной транскрипции.
    
    Использует комбинацию подходов:
    1. Post-processing на уровне приложения
    2. Прямое использование AssemblyAI API
    3. Комбинирование нескольких моделей
    """,
    responses={
        200: {"description": "Результат улучшенной транскрипции"},
        404: {"description": "Урок не найден"}
    }
)
async def test_enhanced_transcription(
    lesson_id: uuid.UUID = Path(..., description="ID урока"),
    use_multiple_approaches: bool = Query(True, description="Использовать несколько подходов"),
    recording_service: RecordingServiceInterface = Depends(get_recording_service)
):
    """Тестировать улучшенную систему транскрипции"""
    
    # For testing, we'll use the existing recording
    recording_id = "74ee9ba8-9942-4ee7-8be9-589ba95aa620"
    lesson_type = "chinese"
    
    try:
        # Test the enhanced transcription system
        if hasattr(recording_service, 'enhanced_service') and recording_service.enhanced_service:
            result = await recording_service.enhanced_service.transcribe_lesson(
                recording_id=recording_id,
                lesson_type=lesson_type,
                use_multiple_approaches=use_multiple_approaches
            )
            
            return {
                "success": True,
                "lesson_id": str(lesson_id),
                "recording_id": recording_id,
                "enhanced_system_used": True,
                "result": result
            }
        else:
            # Fallback to basic system
            result = await recording_service._create_transcript(recording_id, lesson_type)
            
            return {
                "success": True,
                "lesson_id": str(lesson_id),
                "recording_id": recording_id,
                "enhanced_system_used": False,
                "result": result,
                "note": "Enhanced system not available, used basic transcription"
            }
            
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"Error testing enhanced transcription: {str(e)}"
        )

@router.post("/test-enhanced-transcription", response_model=dict)
async def test_enhanced_transcription(
    recording_id: str,
    lesson_type: str = "chinese",
    use_multiple_approaches: bool = True,
    settings: Settings = Depends(get_settings)
):
    """Test enhanced transcription for a recording ID"""
    
    try:
        # Initialize enhanced transcription service
        enhanced_service = EnhancedTranscriptionService(
            recall_api_key=settings.RECALL_API_KEY,
            assemblyai_api_key=settings.ASSEMBLYAI_API_KEY
        )
        
        # Perform enhanced transcription
        result = await enhanced_service.transcribe_lesson(
            recording_id=recording_id,
            lesson_type=lesson_type,
            use_multiple_approaches=use_multiple_approaches
        )
        
        return {
            "success": True,
            "recording_id": recording_id,
            "lesson_type": lesson_type,
            "result": result,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Enhanced transcription test failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/test-dual-language-comparison", response_model=dict)
async def test_dual_language_comparison(
    recording_id: str,
    lesson_type: str = "chinese",
    use_multiple_approaches: bool = True,
    settings: Settings = Depends(get_settings)
):
    """Test dual-language transcription approach with comparison to standard method"""
    
    try:
        # Initialize enhanced transcription service
        enhanced_service = EnhancedTranscriptionService(
            recall_api_key=settings.RECALL_API_KEY,
            assemblyai_api_key=settings.ASSEMBLYAI_API_KEY
        )
        
        # Perform comparative transcription
        result = await enhanced_service.transcribe_lesson_with_comparison(
            recording_id=recording_id,
            lesson_type=lesson_type,
            use_multiple_approaches=use_multiple_approaches
        )
        
        return {
            "success": True,
            "recording_id": recording_id,
            "lesson_type": lesson_type,
            "comparative_result": result,
            "timestamp": datetime.now().isoformat(),
            "processing_info": {
                "standard_method": "YandexGPT single correction",
                "dual_language_method": "YandexGPT dual transcript analysis",
                "comparison_completed": True
            }
        }
        
    except Exception as e:
        logger.error(f"Dual-language comparison test failed: {e}")
        raise HTTPException(status_code=500, detail=str(e)) 