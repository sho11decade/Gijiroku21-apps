# Gijiroku21 Core (Backend)

ローカル完結型議事録アプリの Python Core 実装メモ。

## 実装状況（現在）
 - FastAPI アプリ骨格と共通レスポンス `{ success, data, error }`
 - エンドポイント: `/status`, `/config` (GET/POST), `/record/start`, `/record/stop`, `/transcript/stream`
 - 録音状態管理（thread-safe）、sounddevice 録音（未導入または `GIJIROKU21_FAKE_AUDIO=1` なら無音WAV）
 - ASR パイプライン: Whisper ONNX ロードを試行（環境変数 `GIJIROKU21_WHISPER_ONNX`）。未提供/`GIJIROKU21_FAKE_ASR=1` ではダミー partial/final を配信
 - SSE ブローカー（asyncio.Queue）で transcript イベントを配信
 - デバイス選択: onnxruntime providers から簡易判定（NPU/GPU/CPU/auto）

## 実行方法（開発）
 - 依存インストール（仮想環境推奨）: `pip install fastapi uvicorn pydantic`
 - 実行（リポジトリルートで実行。core直下では `core` モジュールが解決されません）:
	 `uvicorn core.main:app --reload --host 127.0.0.1 --port 8765`
- API ドキュメント: `http://127.0.0.1:8765/docs`

## エンドポイント概要
 - `POST /record/stop` : 録音状態を OFF、ASR を停止。録音開始時刻から duration_sec を算出

## 既知の制約 / TODO
 - 音声キャプチャ: sounddevice が無い場合は無音WAV。実録時は WAV 保存、push は未接続
 - Whisper ONNX 推論: モデルパス未指定/非存在時はダミー。実推論は未実装
 - デバイス検出: onnxruntime providers 依存の簡易判定
 - duration: start/stop 時刻差で算出（実録音長との同期は未調整）

## 次の着手候補
- sounddevice/pyaudio を使った音声キャプチャ実装と保存
- Whisper ONNX 推論を asr_pipeline に統合し、transcript_stream へ publish
- デバイス検出（NPU/CPU/GPU）ロジックの実装
- 最小単体テストの追加（/status, /config, /record, SSE フォーマット）