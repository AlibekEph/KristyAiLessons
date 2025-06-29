"""Local storage service implementation"""

import os
import json
import aiofiles
from typing import Dict, Optional, Any, List
from datetime import datetime
import uuid
import logging

from ..interfaces.storage import (
    StorageServiceInterface,
    StoredFile,
    Lesson
)


logger = logging.getLogger(__name__)


class LocalStorageService(StorageServiceInterface):
    """Local file system storage implementation"""
    
    def __init__(self, storage_path: str = "/app/storage"):
        self.storage_path = storage_path
        self.files_path = os.path.join(storage_path, "files")
        self.json_path = os.path.join(storage_path, "json")
        self.lessons_path = os.path.join(storage_path, "lessons")
        
        # Create directories
        os.makedirs(self.files_path, exist_ok=True)
        os.makedirs(self.json_path, exist_ok=True)
        os.makedirs(self.lessons_path, exist_ok=True)
    
    async def save_file(
        self,
        file_data: bytes,
        filename: str,
        content_type: str = "application/octet-stream",
        metadata: Optional[Dict[str, Any]] = None
    ) -> StoredFile:
        """Save file to local storage"""
        
        file_id = str(uuid.uuid4())
        file_path = os.path.join(self.files_path, file_id)
        
        # Save file
        async with aiofiles.open(file_path, 'wb') as f:
            await f.write(file_data)
        
        # Save metadata
        stored_file = StoredFile(
            id=file_id,
            filename=filename,
            path=file_path,
            size=len(file_data),
            content_type=content_type,
            created_at=datetime.now(),
            metadata=metadata or {}
        )
        
        metadata_path = f"{file_path}.json"
        async with aiofiles.open(metadata_path, 'w') as f:
            await f.write(json.dumps({
                "id": stored_file.id,
                "filename": stored_file.filename,
                "path": stored_file.path,
                "size": stored_file.size,
                "content_type": stored_file.content_type,
                "created_at": stored_file.created_at.isoformat(),
                "metadata": stored_file.metadata
            }))
        
        logger.info(f"Saved file {file_id} ({filename})")
        return stored_file
    
    async def get_file(self, file_id: str) -> bytes:
        """Retrieve file from storage"""
        
        file_path = os.path.join(self.files_path, file_id)
        
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File {file_id} not found")
        
        async with aiofiles.open(file_path, 'rb') as f:
            return await f.read()
    
    async def get_file_url(self, file_id: str, expires_in: int = 3600) -> str:
        """Get temporary URL for file access"""
        
        # For local storage, just return the file path
        # In production, this would generate a signed URL
        return f"file://{os.path.join(self.files_path, file_id)}"
    
    async def delete_file(self, file_id: str) -> bool:
        """Delete file from storage"""
        
        file_path = os.path.join(self.files_path, file_id)
        metadata_path = f"{file_path}.json"
        
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
            if os.path.exists(metadata_path):
                os.remove(metadata_path)
            return True
        except Exception as e:
            logger.error(f"Failed to delete file {file_id}: {e}")
            return False
    
    async def save_lesson(self, lesson: Lesson) -> Lesson:
        """Save or update lesson data"""
        
        lesson_path = os.path.join(self.lessons_path, f"{lesson.id}.json")
        lesson.updated_at = datetime.now()
        
        async with aiofiles.open(lesson_path, 'w') as f:
            await f.write(json.dumps({
                "id": lesson.id,
                "meeting_url": lesson.meeting_url,
                "lesson_type": lesson.lesson_type,
                "student_id": lesson.student_id,
                "teacher_id": lesson.teacher_id,
                "recording_session_id": lesson.recording_session_id,
                "transcription_id": lesson.transcription_id,
                "materials_id": lesson.materials_id,
                "status": lesson.status,
                "created_at": lesson.created_at.isoformat(),
                "updated_at": lesson.updated_at.isoformat(),
                "started_at": lesson.started_at.isoformat() if lesson.started_at else None,
                "ended_at": lesson.ended_at.isoformat() if lesson.ended_at else None,
                "metadata": lesson.metadata
            }))
        
        logger.info(f"Saved lesson {lesson.id}")
        return lesson
    
    async def get_lesson(self, lesson_id: str) -> Optional[Lesson]:
        """Get lesson by ID"""
        
        lesson_path = os.path.join(self.lessons_path, f"{lesson_id}.json")
        
        if not os.path.exists(lesson_path):
            return None
        
        async with aiofiles.open(lesson_path, 'r') as f:
            data = json.loads(await f.read())
        
        return Lesson(
            id=data["id"],
            meeting_url=data["meeting_url"],
            lesson_type=data["lesson_type"],
            student_id=data.get("student_id"),
            teacher_id=data.get("teacher_id"),
            recording_session_id=data.get("recording_session_id"),
            transcription_id=data.get("transcription_id"),
            materials_id=data.get("materials_id"),
            status=data["status"],
            created_at=datetime.fromisoformat(data["created_at"]),
            updated_at=datetime.fromisoformat(data["updated_at"]),
            started_at=datetime.fromisoformat(data["started_at"]) if data.get("started_at") else None,
            ended_at=datetime.fromisoformat(data["ended_at"]) if data.get("ended_at") else None,
            metadata=data.get("metadata", {})
        )
    
    async def list_lessons(
        self,
        student_id: Optional[str] = None,
        teacher_id: Optional[str] = None,
        lesson_type: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Lesson]:
        """List lessons with filters"""
        
        lessons = []
        
        # Read all lesson files
        for filename in os.listdir(self.lessons_path):
            if filename.endswith('.json'):
                lesson = await self.get_lesson(filename[:-5])  # Remove .json extension
                if lesson:
                    # Apply filters
                    if student_id and lesson.student_id != student_id:
                        continue
                    if teacher_id and lesson.teacher_id != teacher_id:
                        continue
                    if lesson_type and lesson.lesson_type != lesson_type:
                        continue
                    if status and lesson.status != status:
                        continue
                    
                    lessons.append(lesson)
        
        # Sort by creation date (newest first)
        lessons.sort(key=lambda x: x.created_at, reverse=True)
        
        # Apply pagination
        return lessons[offset:offset + limit]
    
    async def save_json(self, key: str, data: Dict[str, Any]) -> bool:
        """Save JSON data"""
        
        json_path = os.path.join(self.json_path, f"{key}.json")
        
        try:
            async with aiofiles.open(json_path, 'w') as f:
                await f.write(json.dumps(data))
            return True
        except Exception as e:
            logger.error(f"Failed to save JSON {key}: {e}")
            return False
    
    async def get_json(self, key: str) -> Optional[Dict[str, Any]]:
        """Get JSON data"""
        
        json_path = os.path.join(self.json_path, f"{key}.json")
        
        if not os.path.exists(json_path):
            return None
        
        try:
            async with aiofiles.open(json_path, 'r') as f:
                return json.loads(await f.read())
        except Exception as e:
            logger.error(f"Failed to read JSON {key}: {e}")
            return None 