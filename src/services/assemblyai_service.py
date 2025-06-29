"""AssemblyAI transcription service with automatic language detection"""

import assemblyai as aai
from typing import Dict, Optional, Any, List
from datetime import datetime
import logging
import asyncio

from ..interfaces.transcription import (
    TranscriptionServiceInterface,
    TranscriptionResult,
    TranscriptionStatus,
    TranscriptionSegment,
    TranscriptionWord
)
from ..utils.api_logger import log_api_request, log_api_response
from .language_detection_service import LanguageDetectionService


logger = logging.getLogger(__name__)


class AssemblyAIService(TranscriptionServiceInterface):
    """AssemblyAI service with automatic language detection"""
    
    def __init__(self, api_key: str):
        aai.settings.api_key = api_key
        self.transcriber = aai.Transcriber()
        self.language_detector = LanguageDetectionService()
    
    async def transcribe_audio(
        self,
        audio_url: str,
        language_code: Optional[str] = None,
        enable_speaker_diarization: bool = True,
        enable_punctuation: bool = True,
        enable_formatting: bool = True,
        webhook_url: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> TranscriptionResult:
        """Start transcription of audio file with automatic language optimization"""
        
        # Determine lesson type from metadata if available
        lesson_type = (metadata or {}).get('lesson_type', 'chinese')
        lesson_config = self.language_detector.get_lesson_language_config(lesson_type)
        
        config = aai.TranscriptionConfig(
            speaker_labels=enable_speaker_diarization,
            punctuate=enable_punctuation,
            format_text=enable_formatting,
            language_detection=True,  # Always use automatic detection
            webhook_url=webhook_url
        )
        
        # Only set specific language if explicitly requested and not multilingual lesson
        if language_code and len(lesson_config.get('expected_languages', [])) == 1:
            config.language_code = language_code
            config.language_detection = False
        
        # Use sync method in executor to avoid Future issues
        loop = asyncio.get_event_loop()
        transcript = await loop.run_in_executor(
            None, 
            lambda: self.transcriber.transcribe(audio_url, config=config)
        )
        
        # Convert to our format with intelligent post-processing
        result = self._convert_transcript(transcript, metadata)
        result = await self._apply_intelligent_post_processing(result, lesson_config)
        
        return result
    
    async def transcribe_multilingual(
        self,
        audio_url: str,
        primary_language: str = "ru",
        secondary_languages: Optional[List[str]] = None,
        webhook_url: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> TranscriptionResult:
        """Transcribe multilingual audio with automatic language detection"""
        
        # Determine lesson type from metadata
        lesson_type = (metadata or {}).get('lesson_type', 'chinese')
        
        # AssemblyAI supports automatic language detection
        config = aai.TranscriptionConfig(
            speaker_labels=True,
            punctuate=True,
            format_text=True,
            language_detection=True,  # Enable automatic language detection
            webhook_url=webhook_url
        )
        
        # Use sync method in executor to avoid Future issues
        loop = asyncio.get_event_loop()
        transcript = await loop.run_in_executor(
            None, 
            lambda: self.transcriber.transcribe(audio_url, config=config)
        )
        
        # Convert to our format with intelligent post-processing
        lesson_config = self.language_detector.get_lesson_language_config(lesson_type)
        result = self._convert_transcript(transcript, metadata)
        result = await self._apply_intelligent_post_processing(result, lesson_config)
        
        return result
    
    async def get_transcription_status(self, transcription_id: str) -> TranscriptionResult:
        """Get transcription status"""
        
        loop = asyncio.get_event_loop()
        transcript = await loop.run_in_executor(
            None,
            lambda: self.transcriber.get_transcript(transcription_id)
        )
        return self._convert_transcript(transcript)
    
    async def get_transcription_result(self, transcription_id: str) -> TranscriptionResult:
        """Get completed transcription result"""
        
        loop = asyncio.get_event_loop()
        transcript = await loop.run_in_executor(
            None,
            lambda: self.transcriber.get_transcript(transcription_id)
        )
        
        if transcript.status != aai.TranscriptStatus.completed:
            raise ValueError(f"Transcription {transcription_id} is not completed yet")
        
        return self._convert_transcript(transcript)
    
    async def handle_webhook(self, webhook_data: Dict[str, Any]) -> TranscriptionResult:
        """Handle webhook notifications"""
        
        transcript_id = webhook_data.get("transcript_id")
        if not transcript_id:
            raise ValueError("Invalid webhook data: missing transcript_id")
        
        return await self.get_transcription_status(transcript_id)
    
    async def _apply_intelligent_post_processing(
        self, 
        result: TranscriptionResult, 
        lesson_config: Dict[str, Any]
    ) -> TranscriptionResult:
        """Apply intelligent post-processing based on automatic language analysis"""
        
        if not result.text:
            return result
        
        # Perform language analysis
        language_analysis = self.language_detector.detect_language_mix(result.text)
        
        # Apply algorithmic text improvements
        improved_text = self._apply_text_improvements(result.text, language_analysis)
        
        # Update result
        result.text = improved_text
        
        # Add language analysis to metadata
        result.metadata.update({
            'language_analysis': language_analysis,
            'lesson_config': lesson_config,
            'post_processing_applied': True,
            'quality_metrics': {
                'language_confidence': language_analysis.get('confidence', 0.0),
                'detected_languages': language_analysis.get('detected_languages', []),
                'is_multilingual': language_analysis.get('is_multilingual', False),
                'lesson_type_match': language_analysis.get('lesson_type', 'unknown') == lesson_config.get('lesson_type', 'unknown')
            }
        })
        
        return result
    
    def _apply_text_improvements(
        self, 
        text: str, 
        language_analysis: Dict[str, Any]
    ) -> str:
        """Apply algorithmic text improvements without hardcoded replacements"""
        
        import re
        
        improved_text = text
        
        # 1. Fix spacing issues
        improved_text = re.sub(r'\s+', ' ', improved_text)
        
        # 2. Fix sentence boundaries
        improved_text = re.sub(r'([.!?])\s*([a-zA-Zа-яё\u4e00-\u9fff])', r'\1 \2', improved_text)
        
        # 3. Capitalize sentence starts
        sentences = re.split(r'([.!?]\s+)', improved_text)
        capitalized_sentences = []
        
        for i, sentence in enumerate(sentences):
            if i % 2 == 0 and sentence.strip():  # Actual sentence content
                sentence = sentence.strip()
                if sentence:
                    # Capitalize first character if it's a letter
                    if sentence[0].isalpha():
                        sentence = sentence[0].upper() + sentence[1:] if len(sentence) > 1 else sentence.upper()
            capitalized_sentences.append(sentence)
        
        improved_text = ''.join(capitalized_sentences)
        
        # 4. Remove excessive punctuation
        improved_text = re.sub(r'([.!?]){2,}', r'\1', improved_text)
        
        # 5. Clean up extra whitespace
        improved_text = improved_text.strip()
        
        return improved_text
    
    def _convert_transcript(
        self, 
        transcript: aai.Transcript,
        metadata: Optional[Dict[str, Any]] = None
    ) -> TranscriptionResult:
        """Convert AssemblyAI transcript to our format"""
        
        # Map status
        status_map = {
            aai.TranscriptStatus.queued: TranscriptionStatus.QUEUED,
            aai.TranscriptStatus.processing: TranscriptionStatus.PROCESSING,
            aai.TranscriptStatus.completed: TranscriptionStatus.COMPLETED,
            aai.TranscriptStatus.error: TranscriptionStatus.FAILED
        }
        
        # Extract segments with automatic language detection per segment
        segments = []
        if transcript.words:
            current_segment = None
            current_speaker = None
            
            for word in transcript.words:
                # Check if we need to start a new segment
                if (current_segment is None or 
                    word.speaker != current_speaker or
                    word.start - current_segment.end > 2.0):  # 2 second gap
                    
                    if current_segment:
                        # Add language analysis to segment
                        segment_language_analysis = self.language_detector.detect_language_mix(current_segment.text)
                        current_segment.metadata = {'language_analysis': segment_language_analysis}
                        segments.append(current_segment)
                    
                    current_segment = TranscriptionSegment(
                        text=word.text,
                        start=word.start / 1000.0,  # Convert to seconds
                        end=word.end / 1000.0,
                        confidence=word.confidence,
                        speaker=word.speaker,
                        words=[TranscriptionWord(
                            text=word.text,
                            start=word.start / 1000.0,
                            end=word.end / 1000.0,
                            confidence=word.confidence,
                            speaker=word.speaker
                        )]
                    )
                    current_speaker = word.speaker
                else:
                    # Add word to current segment
                    current_segment.text += f" {word.text}"
                    current_segment.end = word.end / 1000.0
                    current_segment.words.append(
                        TranscriptionWord(
                            text=word.text,
                            start=word.start / 1000.0,
                            end=word.end / 1000.0,
                            confidence=word.confidence,
                            speaker=word.speaker
                        )
                    )
            
            if current_segment:
                # Add language analysis to final segment
                segment_language_analysis = self.language_detector.detect_language_mix(current_segment.text)
                current_segment.metadata = {'language_analysis': segment_language_analysis}
                segments.append(current_segment)
        
        # Use automatic language detection if available, otherwise default
        detected_language = transcript.language_code or "auto"
        
        return TranscriptionResult(
            id=transcript.id,
            status=status_map.get(transcript.status, TranscriptionStatus.QUEUED),
            text=transcript.text or "",
            segments=segments,
            language_code=detected_language,
            duration=transcript.audio_duration / 1000.0 if transcript.audio_duration else None,
            created_at=datetime.now(),  # AssemblyAI doesn't provide this
            completed_at=datetime.now() if transcript.status == aai.TranscriptStatus.completed else None,
            metadata=metadata or {}
        ) 