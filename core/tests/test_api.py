import json
from pathlib import Path
from typing import Iterable

from fastapi.testclient import TestClient

from core.app.utils import paths
from core.main import app

client = TestClient(app)


def _patch_paths(monkeypatch, tmp_path: Path) -> None:
    base = tmp_path / "sandbox"
    monkeypatch.setattr(paths, "documents_root", lambda: base)
    monkeypatch.setattr(paths, "app_root", lambda: base / "Gijiroku21")
    monkeypatch.setattr(paths, "meetings_root", lambda: base / "Gijiroku21" / "meetings")
    monkeypatch.setattr(paths, "config_file", lambda: base / "Gijiroku21" / "config.json")
    monkeypatch.setattr(paths, "meeting_dir", lambda mid: base / "Gijiroku21" / "meetings" / mid.split("-")[0])


def _collect_sse_lines(lines: Iterable[bytes]) -> list[str]:
    decoded = []
    for raw in lines:
        if not raw:
            continue
        decoded.append(raw.decode())
    return decoded


def test_status_returns_envelope(monkeypatch, tmp_path: Path):
    _patch_paths(monkeypatch, tmp_path)

    resp = client.get("/status")
    assert resp.status_code == 200
    body = resp.json()
    assert body["success"] is True
    data = body["data"]
    for key in ["ai_state", "recording", "model", "device", "uptime_sec"]:
        assert key in data


def test_config_roundtrip(monkeypatch, tmp_path: Path):
    _patch_paths(monkeypatch, tmp_path)

    resp = client.get("/config")
    assert resp.status_code == 200
    default_cfg = resp.json()["data"]
    assert default_cfg["language"] == "ja"

    new_cfg = {**default_cfg, "language": "en", "save_audio": False}
    resp2 = client.post("/config", json=new_cfg)
    assert resp2.status_code == 200
    assert resp2.json()["data"]["language"] == "en"
    assert resp2.json()["data"]["save_audio"] is False


def test_record_start_stop(monkeypatch, tmp_path: Path):
    _patch_paths(monkeypatch, tmp_path)

    payload = {"meeting_title": "test", "language": "ja", "save_audio": False}
    resp = client.post("/record/start", json=payload)
    assert resp.status_code == 200
    meeting_id = resp.json()["data"]["meeting_id"]
    assert meeting_id

    resp2 = client.post("/record/stop")
    assert resp2.status_code == 200
    assert resp2.json()["data"]["duration_sec"] == 0


def test_record_stop_writes_audio_when_enabled(monkeypatch, tmp_path: Path):
    _patch_paths(monkeypatch, tmp_path)

    payload = {"meeting_title": "test", "language": "ja", "save_audio": True}
    resp = client.post("/record/start", json=payload)
    meeting_id = resp.json()["data"]["meeting_id"]

    resp2 = client.post("/record/stop")
    assert resp2.status_code == 200

    # meeting_dir uses YYYY-MM-DD from meeting_id
    date_part = "-".join(meeting_id.split("-")[:3])
    audio_path = tmp_path / "sandbox" / "Gijiroku21" / "meetings" / date_part / "audio.wav"
    assert audio_path.exists()


def test_transcript_stream_initial_status(monkeypatch, tmp_path: Path):
    _patch_paths(monkeypatch, tmp_path)

    with client.stream("GET", "/transcript/stream") as response:
        lines = []
        for _ in range(4):
            chunk = next(response.iter_lines())
            if chunk is not None:
                lines.append(chunk)
            if len(lines) >= 2:  # Expect event and data lines before blank separator
                break

    decoded = _collect_sse_lines(lines)
    assert any("stream_ready" in line for line in decoded)
