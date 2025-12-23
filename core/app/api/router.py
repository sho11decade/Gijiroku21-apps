from fastapi import APIRouter

from core.app.api.routes import recording, status

api_router = APIRouter()
api_router.include_router(status.router)
api_router.include_router(recording.router)
