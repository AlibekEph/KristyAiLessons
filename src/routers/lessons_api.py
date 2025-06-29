"""Main router for lesson-related API endpoints."""

from fastapi import APIRouter

from .lessons import get, get_materials, get_transcript, process, record, get_list, test_enhanced_transcription

router = APIRouter(prefix="/lessons", tags=["Lessons"])

# Include all the individual lesson routers
router.include_router(get_list.router)  # List endpoint first (more specific routes first)
router.include_router(record.router)
router.include_router(process.router)
router.include_router(get.router)
router.include_router(get_transcript.router)
router.include_router(get_materials.router)
router.include_router(test_enhanced_transcription.router) 