#!/usr/bin/env python3
"""Script to fix lesson with transcription_id"""

import asyncio
import uuid
from src.database import SessionLocal
from src.services.storage_service import DatabaseStorageService
from src.interfaces.storage import Lesson

async def fix_lesson():
    """Fix lesson with transcription_id"""
    
    lesson_id = "482ec475-7274-4ecc-b65d-e154f9014df3"
    transcription_id = "2240e8c1-c8de-43c6-af69-c4e5913897b8"
    
    # Create database session
    db = SessionLocal()
    storage_service = DatabaseStorageService(db)
    
    try:
        # Get lesson
        lesson = await storage_service.get_lesson(lesson_id)
        if not lesson:
            print(f"Lesson {lesson_id} not found")
            return
        
        print(f"Found lesson: {lesson.id}")
        print(f"Current transcription_id: {lesson.transcription_id}")
        
        # Update transcription_id
        lesson.transcription_id = uuid.UUID(transcription_id)
        lesson.status = "transcribing"
        
        # Save lesson
        updated_lesson = await storage_service.save_lesson(lesson)
        print(f"Updated lesson transcription_id: {updated_lesson.transcription_id}")
        print(f"Updated lesson status: {updated_lesson.status}")
        
    finally:
        db.close()

if __name__ == "__main__":
    asyncio.run(fix_lesson()) 