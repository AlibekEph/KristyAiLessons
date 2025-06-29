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


logger = logging.getLogger(__name__)


class RecallService(RecordingServiceInterface):
    """Recall.ai service implementation"""
    
    def __init__(self, api_key: str, base_url: str = "https://us-west-2.recall.ai/api/v1"):
        self.api_key = api_key
        self.base_url = base_url
        self.headers = {
            "Authorization": f"{api_key}",
            "Content-Type": "application/json"
        }
    
    async def start_recording(
        self,
        meeting_url: str,
        webhook_url: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> RecordingSession:
        """Start recording a meeting via Recall.ai"""
        
        payload = {
            "meeting_url": meeting_url,
            "bot_name": metadata.get("bot_name", "Lesson Recorder") if metadata else "Lesson Recorder",
            "transcription_options": {
                "provider": "assembly_ai"
            },
            "recording": {
                "mode": "speaker_view"
            },
            "real_time_transcription": {
                "destination_url": webhook_url,
                "partial_results": True
            }
        }
        
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
                        "in_call_not_recording": RecordingStatus.RECORDING,
                        "in_call_recording": RecordingStatus.RECORDING,
                        "call_ended": RecordingStatus.COMPLETED,
                        "fatal": RecordingStatus.FAILED
                    }
                    
                    recording_url = None
                    if data.get("recording"):
                        recording_url = data["recording"].get("video_url")
                    
                    return RecordingSession(
                        id=session_id,
                        meeting_url=data.get("meeting_url", ""),
                        status=status_map.get(data["status"], RecordingStatus.PENDING),
                        started_at=datetime.fromisoformat(data["created_at"]) if data.get("created_at") else None,
                        ended_at=datetime.now() if data["status"] == "call_ended" else None,
                        recording_url=recording_url,
                        metadata=data.get("metadata", {})
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