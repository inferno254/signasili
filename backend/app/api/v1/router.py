"""
API Router - Combines all endpoint modules
"""
from fastapi import APIRouter

from app.api.v1.endpoints import auth, learner, teacher, parent, content, bridge, ml, webhooks

api_router = APIRouter()

# Include all endpoint modules
api_router.include_router(auth.router, prefix="/auth", tags=["authentication"])
api_router.include_router(learner.router, prefix="/learner", tags=["learner"])
api_router.include_router(teacher.router, prefix="/teacher", tags=["teacher"])
api_router.include_router(parent.router, prefix="/parent", tags=["parent"])
api_router.include_router(content.router, prefix="/content", tags=["content"])
api_router.include_router(bridge.router, prefix="/bridge", tags=["bridge"])
api_router.include_router(ml.router, prefix="/ml", tags=["machine-learning"])
api_router.include_router(webhooks.router, prefix="/webhooks", tags=["webhooks"])
