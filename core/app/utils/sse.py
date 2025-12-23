from __future__ import annotations

import json
from typing import Optional


def format_sse(data: dict, event: Optional[str] = None) -> str:
    # Minimal SSE formatter: data line plus optional event name, separated by newlines.
    payload = json.dumps(data, ensure_ascii=True)
    lines = []
    if event:
        lines.append(f"event: {event}")
    lines.append(f"data: {payload}")
    lines.append("")  # SSE messages end with a blank line
    return "\n".join(lines)
