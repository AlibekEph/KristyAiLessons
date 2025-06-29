"""AssemblyAI transcription service implementation"""

import assemblyai as aai
from typing import Dict, Optional, Any, List
from datetime import datetime
import logging

from ..interfaces.transcription import (
    TranscriptionServiceInterface,
    TranscriptionResult,
    TranscriptionStatus,
    TranscriptionSegment,
    TranscriptionWord
)
from ..utils.api_logger import log_api_request, log_api_response


logger = logging.getLogger(__name__)


class AssemblyAIService(TranscriptionServiceInterface):
    """AssemblyAI service implementation"""
    
    def __init__(self, api_key: str):
        aai.settings.api_key = api_key
        self.transcriber = aai.Transcriber()
    
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
        """Start transcription of audio file"""
        
        config = aai.TranscriptionConfig(
            speaker_labels=enable_speaker_diarization,
            punctuate=enable_punctuation,
            format_text=enable_formatting,
            language_code=language_code or "ru",
            webhook_url=webhook_url
        )
        
        # Start transcription
        transcript = await self.transcriber.transcribe_async(audio_url, config=config)
        
        # Convert to our format
        return self._convert_transcript(transcript, metadata)
    
    async def transcribe_multilingual(
        self,
        audio_url: str,
        primary_language: str = "ru",
        secondary_languages: Optional[List[str]] = None,
        webhook_url: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> TranscriptionResult:
        """Transcribe multilingual audio"""
        
        # AssemblyAI supports automatic language detection
        config = aai.TranscriptionConfig(
            speaker_labels=True,
            punctuate=True,
            format_text=True,
            language_detection=True,  # Enable language detection
            webhook_url=webhook_url
        )
        
        # Start transcription
        transcript = await self.transcriber.transcribe_async(audio_url, config=config)
        
        # Convert to our format
        return self._convert_transcript(transcript, metadata)
    
    async def get_transcription_status(self, transcription_id: str) -> TranscriptionResult:
        """Get transcription status"""
        
        transcript = await self.transcriber.get_transcript_async(transcription_id)
        return self._convert_transcript(transcript)
    
    async def get_transcription_result(self, transcription_id: str) -> TranscriptionResult:
        """Get completed transcription result"""
        
        transcript = await self.transcriber.get_transcript_async(transcription_id)
        
        if transcript.status != aai.TranscriptStatus.completed:
            raise ValueError(f"Transcription {transcription_id} is not completed yet")
        
        return self._convert_transcript(transcript)
    
    async def handle_webhook(self, webhook_data: Dict[str, Any]) -> TranscriptionResult:
        """Handle webhook notifications"""
        
        transcript_id = webhook_data.get("transcript_id")
        if not transcript_id:
            raise ValueError("Invalid webhook data: missing transcript_id")
        
        return await self.get_transcription_status(transcript_id)
    
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
        
        # Extract segments
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
                segments.append(current_segment)
        
        return TranscriptionResult(
            id=transcript.id,
            status=status_map.get(transcript.status, TranscriptionStatus.QUEUED),
            text=transcript.text or "",
            segments=segments,
            language_code=transcript.language_code or "ru",
            duration=transcript.audio_duration / 1000.0 if transcript.audio_duration else None,
            created_at=datetime.now(),  # AssemblyAI doesn't provide this
            completed_at=datetime.now() if transcript.status == aai.TranscriptStatus.completed else None,
            metadata=metadata or {}
        ) 