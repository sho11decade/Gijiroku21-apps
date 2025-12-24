import json
from pathlib import Path
from typing import List, Optional

from core.app.models.meeting import MeetingDetail, MeetingListItem, MeetingMeta
from core.app.utils import paths


def save_meta(meta: MeetingMeta) -> None:
    paths.ensure_base_dirs()
    dest = paths.meta_file(meta.meeting_id)
    dest.parent.mkdir(parents=True, exist_ok=True)
    with dest.open("w", encoding="utf-8") as f:
        json.dump(meta.model_dump(), f, ensure_ascii=False, indent=2)


def load_meta(meeting_id: str) -> Optional[MeetingMeta]:
    path = paths.meta_file(meeting_id)
    if not path.exists():
        return None
    try:
        with path.open("r", encoding="utf-8") as f:
            data = json.load(f)
        return MeetingMeta(**data)
    except Exception:
        return None


def list_meetings() -> List[MeetingListItem]:
    meetings_root = paths.meetings_root()
    if not meetings_root.exists():
        return []

    items: List[MeetingListItem] = []
    for day_dir in meetings_root.iterdir():
        if not day_dir.is_dir():
            continue
        for meta_path in day_dir.glob("meta.json"):
            meta = load_meta(meta_path.parent.name)
            if not meta:
                continue
            items.append(
                MeetingListItem(
                    meeting_id=meta.meeting_id,
                    title=meta.title,
                    date=day_dir.name,
                    duration_sec=meta.duration_sec,
                )
            )
    # sort by date desc then meeting_id desc
    items.sort(key=lambda x: (x.date, x.meeting_id), reverse=True)
    return items


def load_detail(meeting_id: str) -> Optional[MeetingDetail]:
    meta = load_meta(meeting_id)
    if not meta:
        return None

    transcript_text = None
    summary_text = None
    t_path = paths.transcript_file(meeting_id)
    if t_path.exists():
        transcript_text = t_path.read_text(encoding="utf-8")
    s_path = paths.summary_file(meeting_id)
    if s_path.exists():
        summary_text = s_path.read_text(encoding="utf-8")

    return MeetingDetail(meta=meta, transcript=transcript_text, summary=summary_text)
