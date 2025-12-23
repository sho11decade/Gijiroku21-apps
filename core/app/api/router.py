from fastapi import APIRouter

from core.app.api.routes import config, recording, status, transcript

api_router = APIRouter()
api_router.include_router(status.router)
api_router.include_router(recording.router)
api_router.include_router(config.router)
api_router.include_router(transcript.router)
