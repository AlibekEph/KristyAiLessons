"""Main router for webhook-related API endpoints."""

from fastapi import APIRouter

from .webhooks.recall import router as recall_router
from .webhooks.assemblyai import router as assemblyai_router

router = APIRouter(prefix="/webhooks", tags=["Webhooks"])

# Include all the individual webhook routers
router.include_router(recall_router)
router.include_router(assemblyai_router) 