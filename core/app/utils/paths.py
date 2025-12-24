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
    # meeting_id format: YYYY-MM-DD-HHMMSS... → use YYYY-MM-DD as directory
    parts = meeting_id.split("-")
    if len(parts) >= 3:
        date_part = "-".join(parts[:3])
    else:
        date_part = meeting_id
    return meetings_root() / date_part


def meta_file(meeting_id: str) -> Path:
    return meeting_dir(meeting_id) / "meta.json"


def transcript_file(meeting_id: str) -> Path:
    return meeting_dir(meeting_id) / "transcript.txt"


def summary_file(meeting_id: str) -> Path:
    return meeting_dir(meeting_id) / "summary.md"


def ensure_base_dirs() -> None:
    for path in [app_root(), meetings_root()]:
        path.mkdir(parents=True, exist_ok=True)
