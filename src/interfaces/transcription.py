"""Transcription service interface"""

from abc import ABC, abstractmethod
from typing import Dict, Optional, Any, List
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


class TranscriptionStatus(Enum):
    """Transcription status enum"""
    QUEUED = "queued"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class TranscriptionWord:
    """Individual word in transcription"""
    text: str
    start: float
    end: float
    confidence: float
    speaker: Optional[str] = None


@dataclass
class TranscriptionSegment:
    """Transcription segment"""
    text: str
    start: float
    end: float
    confidence: float
    speaker: Optional[str] = None
    words: List[TranscriptionWord] = field(default_factory=list)
    language: Optional[str] = None


@dataclass
class TranscriptionResult:
    """Transcription result"""
    id: str
    status: TranscriptionStatus
    text: str
    segments: List[TranscriptionSegment] = field(default_factory=list)
    language_code: str = "ru"
    duration: Optional[float] = None
    created_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class TranscriptionServiceInterface(ABC):
    """Interface for transcription services (e.g., AssemblyAI)"""
    
    @abstractmethod
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
        """
        Start transcription of audio file
        
        Args:
            audio_url: URL of the audio file
            language_code: Language code (e.g., 'ru', 'zh', 'en')
            enable_speaker_diarization: Enable speaker identification
            enable_punctuation: Enable punctuation
            enable_formatting: Enable formatting
            webhook_url: URL for webhook notifications
            metadata: Additional metadata
            
        Returns:
            TranscriptionResult object
        """
        pass
    
    @abstractmethod
    async def transcribe_multilingual(
        self,
        audio_url: str,
        primary_language: str = "ru",
        secondary_languages: Optional[List[str]] = None,
        webhook_url: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> TranscriptionResult:
        """
        Transcribe multilingual audio
        
        Args:
            audio_url: URL of the audio file
            primary_language: Primary language code
            secondary_languages: List of secondary language codes
            webhook_url: URL for webhook notifications
            metadata: Additional metadata
            
        Returns:
            TranscriptionResult object
        """
        pass
    
    @abstractmethod
    async def get_transcription_status(self, transcription_id: str) -> TranscriptionResult:
        """
        Get transcription status
        
        Args:
            transcription_id: ID of the transcription
            
        Returns:
            TranscriptionResult object
        """
        pass
    
    @abstractmethod
    async def get_transcription_result(self, transcription_id: str) -> TranscriptionResult:
        """
        Get completed transcription result
        
        Args:
            transcription_id: ID of the transcription
            
        Returns:
            TranscriptionResult object with full text and segments
        """
        pass
    
    @abstractmethod
    async def handle_webhook(self, webhook_data: Dict[str, Any]) -> TranscriptionResult:
        """
        Handle webhook notifications
        
        Args:
            webhook_data: Webhook payload
            
        Returns:
            Updated TranscriptionResult object
        """
        pass 