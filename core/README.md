# Gijiroku21 Core (Backend)

ローカル完結型議事録アプリの Python Core 実装メモ。

## 実装状況（現在）

### API エンドポイント
 - `GET /status` : AI・録音状態、デバイス、アップタイム取得
 - `GET /config` / `POST /config` : 設定の読み込み・保存
 - `POST /record/start` : 会議ID生成、録音開始、ASR パイプライン起動
 - `POST /record/stop` : 録音停止、ASR 停止、メタ情報保存
 - `GET /transcript/stream` : SSE でリアルタイム partial/final を配信
 - `GET /meetings` : 保存済み会議一覧
 - `GET /meetings/{meeting_id}` : 会議詳細（meta.json）取得

### コアロジック
 - **FastAPI 骨格** : 共通レスポンス `{ success, data, error }` で統一
 - **音声キャプチャ** : sounddevice による 16kHz mono PCM 取得。フォールバック時は無音WAV。PCM チャンク を pcm_queue へ push
 - **Whisper ONNX 推論**（実装完了）:
   - tokenizer.json から日本語トークナイザーをロード
   - PCM (16-bit int16) → float32 正規化
   - Log-Mel-Spectrogram 変換（HTK スケール、80ch、3000 フレーム）
   - ONNX encoder/decoder ループで簡易グリーディデコード
   - \<\|startoftranscript\|\>, \<\|ja\|\>, \<\|notimestamps\|\> で日本語固定
   - 環境変数 `GIJIROKU21_FAKE_ASR=1` でダミー fallback
 - **SSE トランスクリプト配信** : partial/final/status イベントを asyncio.Queue 経由で配信
 - **会議メタ保存** : Documents/Gijiroku21/meetings/YYYY-MM-DD/ 配下に meta.json（開始時刻、終了時刻、duration、タイトル）を保存
 - **デバイス検出** : onnxruntime providers 一覧から NPU/GPU/CPU/auto を判定

## 実行方法（開発）

### 依存インストール
```bash
pip install fastapi uvicorn pydantic numpy onnxruntime tokenizers sounddevice
```

### サーバー起動
リポジトリルートから実行（core/ 直下では `core` モジュールが解決されません）:
```bash
uvicorn core.main:app --reload --host 127.0.0.1 --port 8765
```

### API ドキュメント
`http://127.0.0.1:8765/docs`

### テスト実行
```bash
pytest core/tests/ -v
```

環境変数 `GIJIROKU21_FAKE_AUDIO=1` と `GIJIROKU21_FAKE_ASR=1` で、実オーディオ・推論なしにダミーテストが可能

## エンドポイント概要

### 状態・設定
 - `GET /status` : ai_state, recording, model, device, uptime_sec
 - `GET /config` : language (ja/en), save_audio (bool)
 - `POST /config` : 設定保存

### 録音制御
 - `POST /record/start` : meeting_title, language, save_audio を送信。meeting_id を返す
 - `POST /record/stop` : duration_sec を返す。メタ情報を自動保存

### リアルタイム文字起こし・会議情報
 - `GET /transcript/stream` : event: "stream_ready", "heartbeat", "partial", "final", "status" (text/event-stream)
 - `GET /meetings` : 保存済み会議リスト [{ meeting_id, title, start, duration_sec }, ...]
 - `GET /meetings/{meeting_id}` : 会議詳細 { meta: { meeting_id, title, start, end, duration_sec }, ... }

## 既知の制約 / TODO

### モデル・依存
 - **モデルファイル** : core/models/ に whisper-small.onnx, tokenizer.json が必要（環境変数で上書き可）
 - **依存ライブラリ** : onnxruntime, tokenizers, numpy, sounddevice が未インストール時は自動 fallback（ダミー推論）

### 推論精度
 - **グリーディデコード**（1-best）のため複数仮説探索なし
 - **話者分離** : 未実装（将来拡張）
 - **キーワード抽出・決定事項** : 未実装（将来拡張）

### テスト
 - **単体テスト** : pytest で基本エンドポイント、SSE 配信、会議メタ保存を確認済み。実オーディオでの統合テスト要
 - **パフォーマンス** : inference latency, memory usage の計測未実施

## 次の着手候補

### 短期
 - **Transcript/Summary 保存** : `/record/stop` で完全 transcribed テキスト、要約を保存
 - **エクスポート API** : `/export` で TXT / Markdown 形式のダウンロード
 - **より詳細なメタ** : 話者推定、キーワード、決定事項

### 中期
 - **フロントエンド統合** : React ビュー作成、実オーディオ流での SSE テスト
 - **パッケージング** : PyInstaller で core を exe 化し Electron にバンドル
 - **精度向上** : beam search, post-processing ロジック

### 将来
 - **話者分離** : pyannote.audio など別プロセスで実装
 - **多言語** : モデル切り替え対応
 - **NPU/GPU 最適化** : ベンダー固有の推論エンジン試験