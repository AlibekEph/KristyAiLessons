"""Multilingual transcription service using automatic language detection."""

from typing import Dict, Any, Optional
import aiohttp
import logging
from .language_detection_service import LanguageDetectionService

logger = logging.getLogger(__name__)


class MultilingualTranscriptionService:
    """Service for handling multilingual transcription with automatic language detection"""
    
    def __init__(self, recall_api_key: str):
        self.recall_api_key = recall_api_key
        self.base_url = "https://us-west-2.recall.ai/api/v1"
        self.headers = {
            "Authorization": f"Token {recall_api_key}",
            "Content-Type": "application/json"
        }
        self.language_detector = LanguageDetectionService()
    
    def get_lesson_config(self, lesson_type: str) -> Dict[str, Any]:
        """Get optimized configuration for specific lesson type"""
        
        # Get language configuration for lesson type
        lesson_config = self.language_detector.get_lesson_language_config(lesson_type)
        expected_languages = lesson_config.get('expected_languages', ['ru', 'zh'])
        
        # Build AssemblyAI configuration
        config = {
            "provider": {
                "assembly_ai_async": {
                    "language_detection": True,  # Always use automatic language detection
                    "speaker_labels": True,
                    "speakers_expected": 2,
                    "punctuate": True,
                    "format_text": True,
                    "dual_channel": False,
                    "speech_model": "best"  # Use best available model
                }
            }
        }
        
        # Add language-specific optimizations
        if len(expected_languages) == 1:
            # Single language lesson - set specific language code
            config["provider"]["assembly_ai_async"]["language_code"] = expected_languages[0]
        else:
            # Multi-language lesson - use automatic detection
            config["provider"]["assembly_ai_async"]["language_detection"] = True
            # Remove language_code to let AssemblyAI auto-detect
            config["provider"]["assembly_ai_async"].pop("language_code", None)
        
        logger.info(f"Generated config for {lesson_type} lesson: {config}")
        return config
    
    async def create_multilingual_transcript(
        self, 
        recording_id: str, 
        lesson_type: str = "chinese"
    ) -> Optional[Dict[str, Any]]:
        """Create transcript optimized for specific lesson type"""
        
        config = self.get_lesson_config(lesson_type)
        
        logger.info(f"Creating multilingual transcript for recording {recording_id} with {lesson_type} configuration")
        
        async with aiohttp.ClientSession() as session:
            try:
                async with session.post(
                    f"{self.base_url}/recording/{recording_id}/create_transcript/",
                    json=config,
                    headers=self.headers
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        logger.info(f"Successfully created multilingual transcript: {data.get('id')}")
                        return data
                    else:
                        error_text = await response.text()
                        logger.error(f"Failed to create transcript: {response.status} - {error_text}")
                        return None
                        
            except Exception as e:
                logger.error(f"Error creating multilingual transcript: {e}")
                return None
    
    async def get_transcript_with_post_processing(
        self, 
        transcript_id: str
    ) -> Optional[Dict[str, Any]]:
        """Get transcript and apply intelligent post-processing"""
        
        # First get the raw transcript
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(
                    f"{self.base_url}/transcript/{transcript_id}",
                    headers=self.headers
                ) as response:
                    if response.status != 200:
                        return None
                    
                    transcript_meta = await response.json()
                    
                    if transcript_meta.get("status", {}).get("code") != "done":
                        return None
                    
                    download_url = transcript_meta.get("data", {}).get("download_url")
                    if not download_url:
                        return None
                    
                    # Download and post-process transcript
                    async with session.get(download_url) as download_response:
                        if download_response.status != 200:
                            return None
                        
                        transcript_data = await download_response.json()
                        
                        # Apply intelligent post-processing
                        processed_data = self._apply_intelligent_post_processing(transcript_data)
                        return processed_data
                        
            except Exception as e:
                logger.error(f"Error getting transcript: {e}")
                return None
    
    def _apply_intelligent_post_processing(self, transcript_data: Dict[str, Any]) -> Dict[str, Any]:
        """Apply intelligent post-processing using automatic language detection"""
        
        if not isinstance(transcript_data, list) or not transcript_data:
            return transcript_data
        
        # Process each participant's words
        for participant in transcript_data:
            if "words" in participant:
                words = participant["words"]
                
                # Extract text for language analysis
                full_text = " ".join(word.get("text", "") for word in words)
                
                # Perform language analysis
                language_analysis = self.language_detector.detect_language_mix(full_text)
                
                # Apply algorithmic improvements
                improved_words = self._apply_algorithmic_word_improvements(words, language_analysis)
                
                # Add language detection metadata
                participant["words"] = improved_words
                participant["language_analysis"] = language_analysis
                participant["post_processing_applied"] = True
        
        return transcript_data
    
    def _apply_algorithmic_word_improvements(
        self, 
        words: list, 
        language_analysis: Dict[str, Any]
    ) -> list:
        """Apply algorithmic improvements to words without hardcoded replacements"""
        
        improved_words = []
        
        for word in words:
            improved_word = word.copy()
            original_text = word.get("text", "")
            
            # Apply basic text cleaning
            cleaned_text = self._clean_word_text(original_text)
            
            if cleaned_text != original_text:
                improved_word["text"] = cleaned_text
                improved_word["cleaned"] = True
                logger.debug(f"Cleaned word: '{original_text}' -> '{cleaned_text}'")
            
            # Add automatic language detection for individual words
            word_language = self._detect_word_language(cleaned_text)
            improved_word["detected_language"] = word_language
            
            improved_words.append(improved_word)
        
        return improved_words
    
    def _clean_word_text(self, text: str) -> str:
        """Apply basic text cleaning without hardcoded replacements"""
        
        if not text:
            return text
        
        # Remove excessive punctuation
        import re
        cleaned = re.sub(r'[^\w\s\u4e00-\u9fff\u0400-\u04ff]', '', text)
        
        # Remove extra whitespace
        cleaned = re.sub(r'\s+', ' ', cleaned).strip()
        
        # Basic capitalization for sentence starts (heuristic)
        if len(cleaned) > 0:
            cleaned = cleaned[0].upper() + cleaned[1:] if len(cleaned) > 1 else cleaned.upper()
        
        return cleaned
    
    def _detect_word_language(self, text: str) -> str:
        """Detect language of individual word using Unicode ranges"""
        
        if not text:
            return "unknown"
        
        # Check Unicode ranges
        for char in text:
            char_code = ord(char)
            
            # Chinese characters
            if 0x4E00 <= char_code <= 0x9FFF:
                return "zh"
            
            # Cyrillic characters
            if 0x0400 <= char_code <= 0x04FF:
                return "ru"
        
        # If no specific script detected, try language detection on the word
        if len(text) > 2:
            try:
                word_analysis = self.language_detector.detect_language_mix(text)
                detected_languages = word_analysis.get("detected_languages", [])
                if detected_languages:
                    return detected_languages[0]  # Return first detected language
            except Exception:
                pass
        
        # Default to unknown
        return "unknown" 