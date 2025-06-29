"""SQLAlchemy models for the database tables - compatibility layer."""

# Import from the new models structure for backward compatibility
from .models.base import Base
from .models.lesson import Lesson
from .models.transcript import Transcript
from .models.materials import Materials

# Export all models for backward compatibility
__all__ = ["Base", "Lesson", "Transcript", "Materials"] 