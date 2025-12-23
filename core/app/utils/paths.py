from pathlib import Path


APP_FOLDER_NAME = "Gijiroku21"


def documents_root() -> Path:
    return Path.home() / "Documents"


def app_root() -> Path:
    return documents_root() / APP_FOLDER_NAME


def meetings_root() -> Path:
    return app_root() / "meetings"


def config_file() -> Path:
    return app_root() / "config.json"


def meeting_dir(meeting_id: str) -> Path:
    # meeting_id is expected to start with YYYY-MM-DD, so reuse as folder
    return meetings_root() / meeting_id.split("-")[0]


def ensure_base_dirs() -> None:
    for path in [app_root(), meetings_root()]:
        path.mkdir(parents=True, exist_ok=True)
