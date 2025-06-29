"""Recording service interface"""

from abc import ABC, abstractmethod
from typing import Dict, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


class RecordingStatus(Enum):
    """Recording status enum"""
    PENDING = "pending"
    RECORDING = "recording"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class RecordingSession:
    """Recording session data"""
    id: str
    meeting_url: str
    status: RecordingStatus
    started_at: Optional[datetime] = None
    ended_at: Optional[datetime] = None
    recording_url: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class RecordingServiceInterface(ABC):
    """Interface for recording services (e.g., Recall.ai)"""
    
    @abstractmethod
    async def start_recording(
        self, 
        meeting_url: str,
        webhook_url: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> RecordingSession:
        """
        Start recording a meeting
        
        Args:
            meeting_url: URL of the meeting to record
            webhook_url: URL to receive webhook notifications
            metadata: Additional metadata for the recording
            
        Returns:
            RecordingSession object
        """
        pass
    
    @abstractmethod
    async def stop_recording(self, session_id: str) -> RecordingSession:
        """
        Stop an active recording
        
        Args:
            session_id: ID of the recording session
            
        Returns:
            Updated RecordingSession object
        """
        pass
    
    @abstractmethod
    async def get_recording_status(self, session_id: str) -> RecordingSession:
        """
        Get the status of a recording
        
        Args:
            session_id: ID of the recording session
            
        Returns:
            RecordingSession object with current status
        """
        pass
    
    @abstractmethod
    async def download_recording(self, session_id: str) -> bytes:
        """
        Download the recorded audio/video
        
        Args:
            session_id: ID of the recording session
            
        Returns:
            Recording data as bytes
        """
        pass
    
    @abstractmethod
    async def handle_webhook(self, webhook_data: Dict[str, Any]) -> RecordingSession:
        """
        Handle webhook notifications from the recording service
        
        Args:
            webhook_data: Webhook payload
            
        Returns:
            Updated RecordingSession object
        """
        pass 