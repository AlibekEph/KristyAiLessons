"""Recall.ai recording service implementation"""

import aiohttp
import asyncio
from typing import Dict, Optional, Any
from datetime import datetime
import logging

from ..interfaces.recording import (
    RecordingServiceInterface,
    RecordingSession,
    RecordingStatus
)
from ..utils.api_logger import log_api_request, log_api_response
from .multilingual_transcription_service import MultilingualTranscriptionService
from .enhanced_transcription_service import EnhancedTranscriptionService


logger = logging.getLogger(__name__)


class RecallService(RecordingServiceInterface):
    """Recall.ai service implementation"""
    
    def __init__(self, api_key: str, assemblyai_api_key: str = None, base_url: str = "https://us-west-2.recall.ai/api/v1"):
        self.api_key = api_key
        self.assemblyai_api_key = assemblyai_api_key
        self.base_url = base_url
        self.headers = {
            "Authorization": f"Token {api_key}",
            "Content-Type": "application/json"
        }
        # Initialize services
        self.multilingual_service = MultilingualTranscriptionService(api_key)
        
        # Initialize enhanced service if AssemblyAI key is provided
        if assemblyai_api_key:
            self.enhanced_service = EnhancedTranscriptionService(api_key, assemblyai_api_key)
        else:
            self.enhanced_service = None
    
    async def start_recording(
        self,
        meeting_url: str,
        webhook_url: Optional[str],
        metadata: Optional[Dict[str, Any]] = None
    ) -> RecordingSession:
        """Start recording a meeting via Recall.ai"""
        
        payload = {
            "meeting_url": meeting_url,
            "bot_name": metadata.get("bot_name", "Lesson Recorder") if metadata else "Lesson Recorder",
            "recording_config": {
                "transcription": {
                    "provider": {
                        "recall_ai": {}
                    }
                },
                "video_mixed_layout": "speaker_view"
            }
        }
        
        # Note: Bot status webhooks are configured via Recall Dashboard, not through API
        # realtime_endpoints are used for real-time data streaming, not status webhooks
        
        if metadata:
            payload["metadata"] = metadata
        
        # Логируем API запрос
        request_id = await log_api_request(
            method="POST",
            url=f"{self.base_url}/bot",
            headers=self.headers,
            json_data=payload,
            service_name="recall"
        )
        
        async with aiohttp.ClientSession() as session:
            try:
                async with session.post(
                    f"{self.base_url}/bot",
                    json=payload,
                    headers=self.headers
                ) as response:
                    status_code = response.status
                    data = await response.json()
                    
                    # Логируем ответ
                    await log_api_response(
                        request_id=request_id,
                        status_code=status_code,
                        response_data=data,
                        service_name="recall"
                    )
                    
                    response.raise_for_status()
                    
                    return RecordingSession(
                        id=data["id"],
                        meeting_url=meeting_url,
                        status=RecordingStatus.PENDING,
                        started_at=datetime.now(),
                        metadata=metadata or {}
                    )
                    
            except Exception as e:
                # Логируем ошибку
                await log_api_response(
                    request_id=request_id,
                    status_code=getattr(e, 'status', 0),
                    error=str(e),
                    service_name="recall"
                )
                raise
    
    async def stop_recording(self, session_id: str) -> RecordingSession:
        """Stop an active recording"""
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.base_url}/bot/{session_id}/leave_call",
                headers=self.headers
            ) as response:
                response.raise_for_status()
                
                return await self.get_recording_status(session_id)
    
    async def get_recording_status(self, session_id: str) -> RecordingSession:
        """Get the status of a recording"""
        
        # Логируем API запрос
        request_id = await log_api_request(
            method="GET",
            url=f"{self.base_url}/bot/{session_id}",
            headers=self.headers,
            service_name="recall"
        )
        
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(
                    f"{self.base_url}/bot/{session_id}",
                    headers=self.headers
                ) as response:
                    status_code = response.status
                    data = await response.json()
                    
                    # Логируем ответ
                    await log_api_response(
                        request_id=request_id,
                        status_code=status_code,
                        response_data=data,
                        service_name="recall"
                    )
                    
                    response.raise_for_status()
                    
                    status_map = {
                        "joining_call": RecordingStatus.PENDING,
                        "in_call_not_recording": RecordingStatus.PENDING,
                        "in_call_recording": RecordingStatus.RECORDING,
                        "call_ended": RecordingStatus.COMPLETED,
                        "done": RecordingStatus.COMPLETED,
                        "fatal": RecordingStatus.FAILED
                    }
                    
                    # Get current status from status_changes (newest first)
                    status_changes = data.get("status_changes", [])
                    current_status = "unknown"
                    
                    if status_changes:
                        # Get the latest status
                        current_status = status_changes[-1].get("code", "unknown")
                    
                    recording_url = None
                    recordings = data.get("recordings", [])
                    if recordings:
                        # Get first recording's video URL
                        recording = recordings[0]
                        media_shortcuts = recording.get("media_shortcuts", {})
                        video_mixed = media_shortcuts.get("video_mixed", {})
                        if video_mixed:
                            recording_url = video_mixed.get("data", {}).get("download_url")
                    
                    return RecordingSession(
                        id=session_id,
                        meeting_url=data.get("meeting_url", {}).get("meeting_id", ""),
                        status=status_map.get(current_status, RecordingStatus.PENDING),
                        started_at=datetime.fromisoformat(data["join_at"]) if data.get("join_at") else None,
                        ended_at=datetime.now() if current_status in ["call_ended", "done"] else None,
                        recording_url=recording_url,
                        metadata=data.get("metadata", {}),
                        status_changes=status_changes
                    )
                    
            except Exception as e:
                # Логируем ошибку
                await log_api_response(
                    request_id=request_id,
                    status_code=getattr(e, 'status', 0),
                    error=str(e),
                    service_name="recall"
                )
                raise
    
    async def download_recording(self, session_id: str) -> bytes:
        """Download the recorded audio/video"""
        
        # First get the recording URL
        session_data = await self.get_recording_status(session_id)
        
        if not session_data.recording_url:
            raise ValueError(f"No recording available for session {session_id}")
        
        async with aiohttp.ClientSession() as session:
            async with session.get(session_data.recording_url) as response:
                response.raise_for_status()
                return await response.read()
    
    async def get_transcript_data(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get transcript data directly from Recall API"""
        
        # First get bot data to find recording_id
        request_id = await log_api_request(
            method="GET",
            url=f"{self.base_url}/bot/{session_id}",
            headers=self.headers,
            service_name="recall"
        )
        
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(
                    f"{self.base_url}/bot/{session_id}",
                    headers=self.headers
                ) as response:
                    status_code = response.status
                    data = await response.json()
                    
                    await log_api_response(
                        request_id=request_id,
                        status_code=status_code,
                        response_data=data,
                        service_name="recall"
                    )
                    
                    response.raise_for_status()
                    
                    # Check if bot has recordings
                    recordings = data.get("recordings", [])
                    if not recordings:
                        logger.info(f"No recordings found for bot {session_id}")
                        return None
                    
                    # Get the first recording_id
                    recording_id = recordings[0]["id"]
                    logger.info(f"Found recording_id: {recording_id} for bot {session_id}")
                    
                    # Now get recording data to check if transcript exists
                    return await self._get_recording_transcript(recording_id)
                    
            except Exception as e:
                await log_api_response(
                    request_id=request_id,
                    status_code=getattr(e, 'status', 0),
                    error=str(e),
                    service_name="recall"
                )
                raise
    
    async def _get_recording_transcript(self, recording_id: str) -> Optional[Dict[str, Any]]:
        """Get transcript data for a specific recording"""
        
        request_id = await log_api_request(
            method="GET",
            url=f"{self.base_url}/recording/{recording_id}",
            headers=self.headers,
            service_name="recall"
        )
        
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(
                    f"{self.base_url}/recording/{recording_id}",
                    headers=self.headers
                ) as response:
                    status_code = response.status
                    data = await response.json()
                    
                    await log_api_response(
                        request_id=request_id,
                        status_code=status_code,
                        response_data=data,
                        service_name="recall"
                    )
                    
                    response.raise_for_status()
                    
                    # Check if transcript exists
                    transcript_shortcut = data.get("media_shortcuts", {}).get("transcript")
                    
                    if transcript_shortcut and transcript_shortcut.get("data", {}).get("download_url"):
                        # Transcript exists, download it
                        transcript_url = transcript_shortcut["data"]["download_url"]
                        return await self._download_transcript(transcript_url)
                    else:
                        # No transcript exists, need to create one
                        logger.info(f"No transcript found for recording {recording_id}, creating via AssemblyAI")
                        return await self._create_transcript(recording_id)
                    
            except Exception as e:
                await log_api_response(
                    request_id=request_id,
                    status_code=getattr(e, 'status', 0),
                    error=str(e),
                    service_name="recall"
                )
                raise
    
    async def _create_transcript(self, recording_id: str, lesson_type: str = "chinese") -> Optional[Dict[str, Any]]:
        """Create transcript for a recording using enhanced multilingual processing"""
        
        logger.info(f"Creating transcript for recording {recording_id} with lesson type: {lesson_type}")
        
        # Use enhanced service if available
        if self.enhanced_service:
            logger.info("Using enhanced transcription service with multiple approaches")
            return await self.enhanced_service.transcribe_lesson(
                recording_id=recording_id,
                lesson_type=lesson_type,
                use_multiple_approaches=True
            )
        else:
            # Fallback to basic multilingual service
            logger.info("Using basic multilingual transcription service")
            return await self.multilingual_service.create_multilingual_transcript(
                recording_id=recording_id,
                lesson_type=lesson_type
            )
    
    async def get_recording_id(self, bot_id: str) -> Optional[str]:
        """Get recording_id for a bot"""
        
        request_id = await log_api_request(
            method="GET",
            url=f"{self.base_url}/bot/{bot_id}",
            headers=self.headers,
            service_name="recall"
        )
        
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(
                    f"{self.base_url}/bot/{bot_id}",
                    headers=self.headers
                ) as response:
                    status_code = response.status
                    data = await response.json()
                    
                    await log_api_response(
                        request_id=request_id,
                        status_code=status_code,
                        response_data=data,
                        service_name="recall"
                    )
                    
                    response.raise_for_status()
                    
                    recordings = data.get("recordings", [])
                    if recordings:
                        return recordings[0]["id"]
                    
                    return None
                    
            except Exception as e:
                await log_api_response(
                    request_id=request_id,
                    status_code=getattr(e, 'status', 0),
                    error=str(e),
                    service_name="recall"
                )
                raise
    
    async def _download_transcript(self, transcript_url: str) -> Dict[str, Any]:
        """Download transcript from URL"""
        
        async with aiohttp.ClientSession() as session:
            async with session.get(transcript_url) as response:
                response.raise_for_status()
                transcript_data = await response.json()
                return transcript_data
    
    async def get_recording_data(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get full recording data including all media"""
        
        request_id = await log_api_request(
            method="GET",
            url=f"{self.base_url}/bot/{session_id}",
            headers=self.headers,
            service_name="recall"
        )
        
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(
                    f"{self.base_url}/bot/{session_id}",
                    headers=self.headers
                ) as response:
                    status_code = response.status
                    data = await response.json()
                    
                    await log_api_response(
                        request_id=request_id,
                        status_code=status_code,
                        response_data=data,
                        service_name="recall"
                    )
                    
                    response.raise_for_status()
                    return data
                    
            except Exception as e:
                await log_api_response(
                    request_id=request_id,
                    status_code=getattr(e, 'status', 0),
                    error=str(e),
                    service_name="recall"
                )
                raise
    
    async def poll_until_ready(self, session_id: str, timeout: int = 3600, interval: int = 30) -> bool:
        """Poll bot status until recording is done and transcript is ready"""
        
        logger.info(f"Starting polling for bot {session_id}, timeout: {timeout}s, interval: {interval}s")
        
        start_time = datetime.now()
        
        while (datetime.now() - start_time).total_seconds() < timeout:
            try:
                # Get current status
                recording_session = await self.get_recording_status(session_id)
                
                logger.info(f"Bot {session_id} status: {recording_session.status}")
                
                # If recording failed, return False
                if recording_session.status == RecordingStatus.FAILED:
                    logger.error(f"Recording failed for bot {session_id}")
                    return False
                
                # If recording completed, check if transcript is ready
                if recording_session.status == RecordingStatus.COMPLETED:
                    transcript_data = await self.get_transcript_data(session_id)
                    if transcript_data:
                        logger.info(f"Transcript ready for bot {session_id}")
                        return True
                    else:
                        logger.info(f"Recording done but transcript not ready yet for bot {session_id}")
                
                # Wait before next poll
                await asyncio.sleep(interval)
                
            except Exception as e:
                logger.error(f"Error during polling for bot {session_id}: {e}")
                await asyncio.sleep(interval)
        
        logger.warning(f"Polling timeout reached for bot {session_id}")
        return False
    
    async def handle_webhook(self, webhook_data: Dict[str, Any]) -> RecordingSession:
        """Handle webhook notifications from Recall.ai"""
        
        event_type = webhook_data.get("event")
        bot_id = webhook_data.get("data", {}).get("bot_id")
        
        if not bot_id:
            raise ValueError("Invalid webhook data: missing bot_id")
        
        # Log the event
        logger.info(f"Received webhook event '{event_type}' for bot {bot_id}")
        
        # Get current status
        return await self.get_recording_status(bot_id)
    
    async def get_bot_data(self, bot_id: str) -> Optional[Dict[str, Any]]:
        """Get bot data including media shortcuts"""
        
        request_id = await log_api_request(
            method="GET",
            url=f"{self.base_url}/bot/{bot_id}",
            headers=self.headers,
            service_name="recall"
        )
        
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(
                    f"{self.base_url}/bot/{bot_id}",
                    headers=self.headers
                ) as response:
                    status_code = response.status
                    data = await response.json()
                    
                    await log_api_response(
                        request_id=request_id,
                        status_code=status_code,
                        response_data=data,
                        service_name="recall"
                    )
                    
                    response.raise_for_status()
                    return data
                    
            except Exception as e:
                await log_api_response(
                    request_id=request_id,
                    status_code=getattr(e, 'status', 0),
                    error=str(e),
                    service_name="recall"
                )
                logger.error(f"Failed to get bot data for {bot_id}: {e}")
                return None 