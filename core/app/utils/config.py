import json
from pathlib import Path
from typing import Optional

from core.app.models.config import AppConfig
from core.app.utils import paths


def _write_default(target: Path) -> AppConfig:
    config = AppConfig()
    with target.open("w", encoding="utf-8") as f:
        json.dump(config.model_dump(), f, ensure_ascii=True, indent=2)
    return config


def load_config() -> AppConfig:
    paths.ensure_base_dirs()
    cfg_path = paths.config_file()
    if not cfg_path.exists():
        return _write_default(cfg_path)

    try:
        with cfg_path.open("r", encoding="utf-8") as f:
            data = json.load(f)
        return AppConfig(**data)
    except Exception:
        return _write_default(cfg_path)


def save_config(config: AppConfig) -> AppConfig:
    paths.ensure_base_dirs()
    cfg_path = paths.config_file()
    with cfg_path.open("w", encoding="utf-8") as f:
        json.dump(config.model_dump(), f, ensure_ascii=True, indent=2)
    return config
