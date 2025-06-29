"""Storage service interface"""

from abc import ABC, abstractmethod
from typing import Dict, Optional, Any, List, BinaryIO
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


class StorageType(Enum):
    """Storage type enum"""
    LOCAL = "local"
    S3 = "s3"
    GCS = "gcs"
    AZURE = "azure"


@dataclass
class StoredFile:
    """Stored file metadata"""
    id: str
    filename: str
    path: str
    size: int
    content_type: str
    created_at: datetime
    metadata: Dict[str, Any] = field(default_factory=dict)
    url: Optional[str] = None


@dataclass
class Lesson:
    """Lesson entity"""
    id: str
    meeting_url: str
    lesson_type: str  # "chinese", "english"
    student_id: Optional[str] = None
    teacher_id: Optional[str] = None
    recording_session_id: Optional[str] = None
    transcription_id: Optional[str] = None
    materials_id: Optional[str] = None
    status: str = "pending"
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    ended_at: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class StorageServiceInterface(ABC):
    """Interface for storage services"""
    
    @abstractmethod
    async def save_file(
        self,
        file_data: bytes,
        filename: str,
        content_type: str = "application/octet-stream",
        metadata: Optional[Dict[str, Any]] = None
    ) -> StoredFile:
        """
        Save file to storage
        
        Args:
            file_data: File data as bytes
            filename: Name of the file
            content_type: MIME type of the file
            metadata: Additional metadata
            
        Returns:
            StoredFile object with file information
        """
        pass
    
    @abstractmethod
    async def get_file(self, file_id: str) -> bytes:
        """
        Retrieve file from storage
        
        Args:
            file_id: ID of the file
            
        Returns:
            File data as bytes
        """
        pass
    
    @abstractmethod
    async def get_file_url(self, file_id: str, expires_in: int = 3600) -> str:
        """
        Get temporary URL for file access
        
        Args:
            file_id: ID of the file
            expires_in: URL expiration time in seconds
            
        Returns:
            Temporary URL for file access
        """
        pass
    
    @abstractmethod
    async def delete_file(self, file_id: str) -> bool:
        """
        Delete file from storage
        
        Args:
            file_id: ID of the file
            
        Returns:
            True if deleted successfully
        """
        pass
    
    @abstractmethod
    async def save_lesson(self, lesson: Lesson) -> Lesson:
        """
        Save or update lesson data
        
        Args:
            lesson: Lesson object
            
        Returns:
            Saved lesson object
        """
        pass
    
    @abstractmethod
    async def get_lesson(self, lesson_id: str) -> Optional[Lesson]:
        """
        Get lesson by ID
        
        Args:
            lesson_id: ID of the lesson
            
        Returns:
            Lesson object or None
        """
        pass
    
    @abstractmethod
    async def list_lessons(
        self,
        student_id: Optional[str] = None,
        teacher_id: Optional[str] = None,
        lesson_type: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Lesson]:
        """
        List lessons with filters
        
        Args:
            student_id: Filter by student
            teacher_id: Filter by teacher
            lesson_type: Filter by type
            status: Filter by status
            limit: Maximum number of results
            offset: Offset for pagination
            
        Returns:
            List of lessons
        """
        pass
    
    @abstractmethod
    async def save_json(self, key: str, data: Dict[str, Any]) -> bool:
        """
        Save JSON data
        
        Args:
            key: Unique key for the data
            data: Dictionary to save
            
        Returns:
            True if saved successfully
        """
        pass
    
    @abstractmethod
    async def get_json(self, key: str) -> Optional[Dict[str, Any]]:
        """
        Get JSON data
        
        Args:
            key: Key to retrieve
            
        Returns:
            Dictionary or None
        """
        pass 