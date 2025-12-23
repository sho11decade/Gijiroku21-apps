# Gijiroku21 Core (Backend)

ローカル完結型議事録アプリの Python Core 実装メモ。

## 実装状況（現在）
- FastAPI アプリ骨格と共通レスポンス `{ success, data, error }`
- エンドポイント: `/status`, `/config` (GET/POST), `/record/start`, `/record/stop`, `/transcript/stream`
- 録音状態管理（thread-safe）、ダミー audio capture フック、ダミー ASR パイプライン（partial/final イベント送信）
- SSE ブローカー（asyncio.Queue）で transcript イベントを配信
- デバイス選択はスタブ（`auto` 固定）

## 実行方法（開発）
- 依存インストール（仮想環境推奨）: `pip install fastapi uvicorn pydantic`
- 実行: `uvicorn main:app --reload --host 127.0.0.1 --port 8765`
- API ドキュメント: `http://127.0.0.1:8765/docs`

## エンドポイント概要
- `GET /status` : ai_state (`ready`/`listening`)、recording、model、device、uptime を返却
- `POST /record/start` : meeting_id を発行し録音状態を ON、ダミー ASR を開始
- `POST /record/stop` : 録音状態を OFF、ASR を停止（duration は仮で 0）
- `GET /transcript/stream` : SSE。initial `stream_ready` → heartbeat 5s。ASR が partial/final を publish
- `GET/POST /config` : Documents/Gijiroku21/config.json の読込・保存

## 既知の制約 / TODO
- 音声キャプチャは未実装（audio_capture は空のフック）
- Whisper ONNX 推論は未統合（asr_pipeline はダミー送信のみ）
- デバイス検出は固定値 `auto`
- duration 計測なし

## 次の着手候補
- sounddevice/pyaudio を使った音声キャプチャ実装と保存
- Whisper ONNX 推論を asr_pipeline に統合し、transcript_stream へ publish
- デバイス検出（NPU/CPU/GPU）ロジックの実装
- 最小単体テストの追加（/status, /config, /record, SSE フォーマット）