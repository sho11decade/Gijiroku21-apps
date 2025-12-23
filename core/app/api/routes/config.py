from fastapi import APIRouter

from core.app.models.config import AppConfig
from core.app.models.response import Envelope, success_response
from core.app.utils import config as config_utils

router = APIRouter(prefix="/config", tags=["config"])


@router.get("", response_model=Envelope[AppConfig])
async def get_config() -> Envelope[AppConfig]:
    cfg = config_utils.load_config()
    return success_response(cfg)


@router.post("", response_model=Envelope[AppConfig])
async def update_config(payload: AppConfig) -> Envelope[AppConfig]:
    cfg = config_utils.save_config(payload)
    return success_response(cfg)
