"""Database storage service implementation."""

import uuid
from typing import List, Optional, Dict, Any

from sqlalchemy.orm import Session

from .. import crud, schemas
from ..interfaces.storage import StorageServiceInterface, Lesson, StoredFile

class DatabaseStorageService(StorageServiceInterface):
    def __init__(self, db: Session):
        self.db = db

    async def get_lesson(self, lesson_id: str) -> Optional[Lesson]:
        db_lesson = crud.get_lesson(self.db, lesson_id=uuid.UUID(lesson_id))
        if db_lesson:
            return Lesson.from_orm(db_lesson)
        return None

    async def list_lessons(self, skip: int = 0, limit: int = 100) -> List[Lesson]:
        db_lessons = crud.get_lessons(self.db, skip=skip, limit=limit)
        return [Lesson.from_orm(lesson) for lesson in db_lessons]

    async def save_lesson(self, lesson: Lesson) -> Lesson:
        # Check if lesson already exists
        if lesson.id:
            existing_lesson = crud.get_lesson(self.db, lesson_id=lesson.id)
            if existing_lesson:
                # Update existing lesson
                lesson_data = lesson.dict(exclude_unset=True)
                db_lesson = crud.update_lesson(self.db, lesson_id=lesson.id, lesson_data=lesson_data)
                return Lesson.from_orm(db_lesson)
        
        # Create new lesson
        lesson_data = schemas.LessonCreate(**lesson.dict())
        db_lesson = crud.create_lesson(self.db, lesson=lesson_data)
        return Lesson.from_orm(db_lesson)

    async def save_transcript(self, lesson_id: str, transcript_data: dict) -> None:
        transcript = schemas.TranscriptCreate(**transcript_data)
        crud.create_lesson_transcript(self.db, transcript=transcript, lesson_id=uuid.UUID(lesson_id))

    async def save_materials(self, lesson_id: str, materials_data: dict) -> None:
        materials = schemas.MaterialsCreate(**materials_data)
        crud.create_lesson_materials(self.db, materials=materials, lesson_id=uuid.UUID(lesson_id))

    # File storage methods - not implemented for database service
    async def save_file(
        self,
        file_data: bytes,
        filename: str,
        content_type: str = "application/octet-stream",
        metadata: Optional[Dict[str, Any]] = None
    ) -> StoredFile:
        """Save file - not implemented for database service"""
        raise NotImplementedError("File storage not implemented in DatabaseStorageService")

    async def get_file(self, file_id: str) -> bytes:
        """Get file - not implemented for database service"""
        raise NotImplementedError("File storage not implemented in DatabaseStorageService")

    async def get_file_url(self, file_id: str, expires_in: int = 3600) -> str:
        """Get file URL - not implemented for database service"""
        raise NotImplementedError("File storage not implemented in DatabaseStorageService")

    async def delete_file(self, file_id: str) -> bool:
        """Delete file - not implemented for database service"""
        raise NotImplementedError("File storage not implemented in DatabaseStorageService")

    async def save_json(self, key: str, data: Dict[str, Any]) -> bool:
        """Save JSON data using transcript and materials tables"""
        try:
            if key.startswith("transcript_"):
                lesson_id = key.replace("transcript_", "")
                await self.save_transcript(lesson_id, data)
            elif key.startswith("materials_"):
                lesson_id = key.replace("materials_", "")
                await self.save_materials(lesson_id, data)
            return True
        except Exception:
            return False

    async def get_json(self, key: str) -> Optional[Dict[str, Any]]:
        """Get JSON data from transcript and materials tables"""
        try:
            if key.startswith("transcript_"):
                lesson_id = key.replace("transcript_", "")
                transcript = crud.get_lesson_transcript(self.db, uuid.UUID(lesson_id))
                if transcript:
                    return {
                        "text": transcript.text,
                        "segments": transcript.segments,
                        "language_code": transcript.language_code,
                        "duration": transcript.duration
                    }
            elif key.startswith("materials_"):
                lesson_id = key.replace("materials_", "")
                materials = crud.get_lesson_materials(self.db, uuid.UUID(lesson_id))
                if materials:
                    return {
                        "original_transcript": materials.original_transcript,
                        "corrected_transcript": materials.corrected_transcript,
                        "summary": materials.summary,
                        "homework": materials.homework,
                        "notes": materials.notes,
                        "key_vocabulary": materials.key_vocabulary
                    }
            return None
        except Exception:
            return None 