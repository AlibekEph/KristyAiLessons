"""Test endpoints for language detection service."""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Dict, Any, Optional

from ...services.language_detection_service import LanguageDetectionService
from ...services.enhanced_transcription_service import EnhancedTranscriptionService
from ...config import Settings

router = APIRouter(prefix="/test", tags=["test"])


class LanguageTestRequest(BaseModel):
    text: str
    lesson_type: Optional[str] = "chinese"


class TranscriptionTestRequest(BaseModel):
    recording_id: str
    lesson_type: Optional[str] = "chinese"
    use_multiple_approaches: Optional[bool] = True
    create_unified_timeline: Optional[bool] = True


@router.post("/language-detection")
async def test_language_detection(request: LanguageTestRequest) -> Dict[str, Any]:
    """Test automatic language detection on text"""
    
    try:
        language_detector = LanguageDetectionService()
        
        # Perform language analysis
        detection_result = language_detector.detect_language_mix(request.text)
        
        # Get lesson configuration
        lesson_config = language_detector.get_lesson_language_config(request.lesson_type)
        
        # Calculate quality score
        quality_score = language_detector.calculate_quality_score(
            detection_result, request.lesson_type
        )
        
        return {
            "success": True,
            "input": {
                "text": request.text,
                "lesson_type": request.lesson_type
            },
            "detection_result": detection_result,
            "lesson_config": lesson_config,
            "quality_score": quality_score,
            "analysis": {
                "text_length": len(request.text),
                "word_count": len(request.text.split()),
                "has_chinese_script": any(0x4E00 <= ord(char) <= 0x9FFF for char in request.text),
                "has_cyrillic_script": any(0x0400 <= ord(char) <= 0x04FF for char in request.text),
                "has_latin_script": any(0x0041 <= ord(char) <= 0x007A for char in request.text.lower())
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Language detection failed: {str(e)}")


@router.post("/enhanced-transcription")
async def test_enhanced_transcription(request: TranscriptionTestRequest) -> Dict[str, Any]:
    """Test enhanced transcription service with automatic language detection"""
    
    try:
        settings = Settings()
        
        # Initialize enhanced transcription service
        enhanced_service = EnhancedTranscriptionService(
            recall_api_key=settings.RECALL_API_KEY,
            assemblyai_api_key=settings.ASSEMBLYAI_API_KEY
        )
        
        # Perform transcription
        result = await enhanced_service.transcribe_lesson(
            recording_id=request.recording_id,
            lesson_type=request.lesson_type,
            use_multiple_approaches=request.use_multiple_approaches
        )
        
        # Enhance result with language detection on unified text if available
        if result.get("unified_timeline") and result.get("text"):
            language_detector = LanguageDetectionService()
            unified_language_analysis = language_detector.detect_language_mix(result["text"])
            result["unified_language_analysis"] = unified_language_analysis
        
        return {
            "success": True,
            "input": {
                "recording_id": request.recording_id,
                "lesson_type": request.lesson_type,
                "use_multiple_approaches": request.use_multiple_approaches,
                "create_unified_timeline": request.create_unified_timeline
            },
            "transcription_result": result,
            "info": {
                "has_unified_timeline": result.get("unified_timeline", False),
                "total_words": result.get("total_words", 0),
                "approaches_used": list(result.get("approaches_analysis", {}).keys())
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Enhanced transcription failed: {str(e)}")


@router.get("/language-configs")
async def get_language_configs() -> Dict[str, Any]:
    """Get all available language configurations"""
    
    try:
        language_detector = LanguageDetectionService()
        
        configs = {}
        for lesson_type in ["chinese", "english"]:
            configs[lesson_type] = language_detector.get_lesson_language_config(lesson_type)
        
        return {
            "success": True,
            "available_lesson_types": list(configs.keys()),
            "configurations": configs,
            "script_ranges": language_detector.SCRIPT_RANGES,
            "supported_lesson_types": language_detector.LESSON_TYPES
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get language configs: {str(e)}")


@router.post("/compare-text-quality")
async def compare_text_quality(
    text1: str,
    text2: str,
    lesson_type: str = "chinese"
) -> Dict[str, Any]:
    """Compare quality of two transcription texts"""
    
    try:
        language_detector = LanguageDetectionService()
        
        # Analyze both texts
        analysis1 = language_detector.detect_language_mix(text1)
        analysis2 = language_detector.detect_language_mix(text2)
        
        # Calculate quality scores
        score1 = language_detector.calculate_quality_score(analysis1, lesson_type)
        score2 = language_detector.calculate_quality_score(analysis2, lesson_type)
        
        # Determine winner
        winner = "text1" if score1 > score2 else "text2" if score2 > score1 else "tie"
        
        return {
            "success": True,
            "comparison": {
                "text1": {
                    "text": text1,
                    "analysis": analysis1,
                    "quality_score": score1
                },
                "text2": {
                    "text": text2,
                    "analysis": analysis2,
                    "quality_score": score2
                },
                "winner": winner,
                "score_difference": abs(score1 - score2),
                "lesson_type": lesson_type
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Text comparison failed: {str(e)}")


@router.get("/health")
async def health_check() -> Dict[str, Any]:
    """Health check for language detection service"""
    
    try:
        language_detector = LanguageDetectionService()
        
        # Test with sample text
        test_text = "Как дела будут? 你好吗？ Hello there!"
        result = language_detector.detect_language_mix(test_text)
        
        return {
            "success": True,
            "service_status": "healthy",
            "test_result": result,
            "capabilities": {
                "supports_multilingual": True,
                "supports_chinese": True,
                "supports_russian": True,
                "supports_english": True,
                "automatic_detection": True,
                "no_hardcoded_words": True
            }
        }
        
    except Exception as e:
        return {
            "success": False,
            "service_status": "unhealthy",
            "error": str(e)
        } 