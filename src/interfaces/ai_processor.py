"""AI processor interface"""

from abc import ABC, abstractmethod
from typing import Dict, Optional, Any, List
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class LessonMaterials:
    """Generated lesson materials"""
    lesson_id: str
    original_transcript: str
    corrected_transcript: str
    summary: str
    homework: str
    notes: str
    key_vocabulary: List[Dict[str, str]] = field(default_factory=list)  # [{"chinese": "你好", "pinyin": "nǐ hǎo", "translation": "привет"}]
    created_at: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AIProcessingRequest:
    """Request for AI processing"""
    transcript: str
    lesson_type: str  # "chinese", "english"
    student_level: Optional[str] = None  # "beginner", "intermediate", "advanced"
    lesson_duration: Optional[float] = None
    additional_context: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class AIProcessorInterface(ABC):
    """Interface for AI processing services (e.g., YandexGPT)"""
    
    @abstractmethod
    async def process_lesson(
        self,
        request: AIProcessingRequest
    ) -> LessonMaterials:
        """
        Process lesson transcript and generate materials
        
        Args:
            request: Processing request with transcript and metadata
            
        Returns:
            LessonMaterials with generated content
        """
        pass
    
    @abstractmethod
    async def correct_multilingual_transcript(
        self,
        transcript: str,
        source_language: str = "ru",
        target_languages: Optional[List[str]] = None
    ) -> str:
        """
        Correct multilingual transcript by adding proper characters and pinyin
        
        Args:
            transcript: Original transcript
            source_language: Primary language of the transcript
            target_languages: Languages to correct (e.g., ["zh"])
            
        Returns:
            Corrected transcript with proper characters and pinyin
        """
        pass
    
    @abstractmethod
    async def generate_summary(
        self,
        transcript: str,
        lesson_type: str,
        student_level: Optional[str] = None
    ) -> str:
        """
        Generate lesson summary
        
        Args:
            transcript: Lesson transcript
            lesson_type: Type of lesson
            student_level: Student's level
            
        Returns:
            Structured lesson summary
        """
        pass
    
    @abstractmethod
    async def generate_homework(
        self,
        transcript: str,
        lesson_type: str,
        student_level: Optional[str] = None,
        previous_homework: Optional[str] = None
    ) -> str:
        """
        Generate homework based on lesson content
        
        Args:
            transcript: Lesson transcript
            lesson_type: Type of lesson
            student_level: Student's level
            previous_homework: Previous homework for continuity
            
        Returns:
            Homework assignments and recommendations
        """
        pass
    
    @abstractmethod
    async def extract_vocabulary(
        self,
        transcript: str,
        lesson_type: str
    ) -> List[Dict[str, str]]:
        """
        Extract key vocabulary from lesson
        
        Args:
            transcript: Lesson transcript
            lesson_type: Type of lesson
            
        Returns:
            List of vocabulary items with translations
        """
        pass 