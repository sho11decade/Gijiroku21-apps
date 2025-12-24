# Gijiroku21

## 概要
Gijiroku21は、PC内で完結するローカルAI議事録アプリケーションです。NPU / CPU / GPUを活用した`Whisper`相当の音声認識を行い、音声をクラウドに送信せずにリアルタイムで文字起こし・要約・保存ができます。すべての処理はElectronベースのGUIとPython Coreの疎結合構成で進行し、非技術者でも直感的に使える操作性を目指しています。

## 想定ユーザー・利用シーン
- 個人ユーザーや中小企業、自治会・学校などの非公開会議
- 定例会議、打ち合わせ、自治会総会やインタビュー（将来）
これらの場面で、会議録音を外部に送らずに記録しながら、参加者がリアルタイムで内容を追えることが狙いです。

## 主な機能
- リアルタイム文字起こしとストリーミング風UI
- 話者推定・区別と会議中の確認
- 議事録全文のローカル保存と箇条書き要約
- TXT / Markdown 形式でのエクスポート（PDF / Word は将来対応）
- 録音データの任意保存と高速な再生

## 技術構成と特徴
フロントエンドは`React` + `Electron` + TypeScriptで構成し、`Zustand`やHooksを使った状態管理で軽いUIを実現します。バックエンドは`Python`で実装され、`FastAPI`経由で音声取得・ONNX Runtime推論・ポストプロセッシングを行います。トークナイザーやモデルはローカルにパッケージされ、FP16 / INT8やNPU優先制御を見据えた設計です。詳細なアーキテクチャは [docs/Architecture.md](docs/Architecture.md) に記載しています。

## 使い方（想定）
1. Windowsインストーラからアプリをインストールし、起動する。
2. ホーム画面でマイクを選び、録音を開始する。
3. 文字起こしが数秒以内に表示され、リアルタイムで確認できる。必要に応じて要約・保存を行う。
4. 会議終了後、保存フォルダ（例: Documents/Gijiroku21/meetings/<日付>）から文字起こしや要約ファイルを参照・編集する。

## データとプライバシー
すべての音声・テキストはローカルストレージにのみ保存され、クラウドへの送信や外部API呼び出しは行いません。デフォルトでは Documents/Gijiroku21/ 以下に音声ファイル・文字起こし・要約を保存し、ユーザーが直接操作できます。またアンインストール時もデータは保持されます。

## 開発と資料
プロトタイプ段階では`PyInstaller`を使ってPython Coreを単体exe化し、フロントエンドからはIPC / HTTP（localhost）で制御します。テスト重視のPythonモジュールと疎結合なUIによって、モデル差し替えや将来のmacOS / Linux対応を見据えます。要件や仕様の全体像は [docs/DevPlan.md](docs/DevPlan.md) を参照してください。

## 今後の展望
- 話者分離・決定事項 / ToDo 抽出の精度向上
- PDF / Word 形式のエクスポート
- NPUベンダーごとの最適化と自動アップデート通知
- macOS / Linux への拡張

## 実装進捗

### バックエンド（Python Core）
**状態：実装完了（~80%）**

#### 完了項目
- FastAPI による基本骨格とレスポンス統一形式 `{ success, data, error }`
- 音声キャプチャ（sounddevice + PCM キュー）
- **Whisper ONNX 統合**：tokenizer.json ロード、log-mel 変換、グリーディデコード実装
- SSE によるリアルタイム partial/final 配信
- 会議メタ自動保存（meta.json：開始時刻、終了時刻、duration）
- `/status`, `/config`, `/record/start`, `/record/stop`, `/transcript/stream`, `/meetings`, `/meetings/{id}` エンドポイント実装
- pytest による基本テスト

#### 今後の予定（優先順）
1. Transcript 完全文・要約の保存と `/export` エンドポイント
2. テキスト後処理（日本語整形）
3. 実オーディオでの統合テスト

### フロントエンド（React + Electron）
**状態：未実装**

#### 予定項目
1. React + TypeScript + Zustand スケルトン
2. ホーム画面、リアルタイム文字起こし表示
3. 会議一覧・詳細、設定画面
4. SSE リスナー統合
5. Electron ウィンドウ設定

### 全体スケジュール目安
- Core 最終化：2～3週間
- Frontend 開発・統合テスト：3～4週間
- パッケージング（PyInstaller + Electron）：1～2週間
- インストーラー・リリース準備：1～2週間

## 開発・運用ガイド

### リポジトリ構成
```
Gijiroku21/
├── core/                          # Python Core（FastAPI）
│   ├── app/
│   │   ├── api/
│   │   │   ├── routes/           # エンドポイント実装
│   │   │   └── dependencies.py
│   │   ├── models/               # Pydantic モデル
│   │   ├── services/             # ビジネスロジック
│   │   │   ├── audio_capture.py
│   │   │   ├── asr_pipeline.py
│   │   │   ├── whisper_engine.py  # ONNX 推論
│   │   │   └── recording_state.py
│   │   └── utils/                # ユーティリティ
│   │       ├── paths.py
│   │       ├── storage.py        # meta.json 管理
│   │       ├── pcm_queue.py
│   │       ├── transcript_stream.py
│   │       └── device.py
│   ├── models/                   # whisper-small.onnx, tokenizer.json
│   ├── tests/
│   │   └── test_api.py
│   ├── main.py                   # FastAPI app エントリポイント
│   └── README.md                 # Core 実装ガイド
├── frontend/                      # React + Electron（未実装）
├── docs/
│   ├── DevPlan.md               # 要件仕様・進捗
│   ├── Architecture.md           # システム設計
│   ├── APIDevPlan.md            # API 仕様
│   └── BackendDevPlan.md        # Core 詳細仕様
├── scripts/                       # ビルド・ヘルパースクリプト
├── README.md
└── pytest.ini
```

### Core 開発（Linux/macOS でも可能）
```bash
# リポジトリ直下で
uvicorn core.main:app --reload --host 127.0.0.1 --port 8765

# テスト
pytest core/tests/ -v

# ダミーモード（オーディオ/推論なし）
GIJIROKU21_FAKE_AUDIO=1 GIJIROKU21_FAKE_ASR=1 pytest core/tests/ -v
```

### API ドキュメント
起動後 `http://127.0.0.1:8765/docs` にアクセス

### 設定ファイル
- `config.json` : Documents/Gijiroku21/ 直下（ユーザー編集可）
- `meta.json` : Documents/Gijiroku21/meetings/YYYY-MM-DD/ 配下（自動生成）

## ドキュメント・参考資料

- **要件仕様・開発計画** : [docs/DevPlan.md](docs/DevPlan.md)
- **システムアーキテクチャ** : [docs/Architecture.md](docs/Architecture.md)
- **API 仕様** : [docs/APIDevPlan.md](docs/APIDevPlan.md)
- **Core 実装ガイド** : [core/README.md](core/README.md)
- **Backend 詳細仕様** : [docs/BackendDevPlan.md](docs/BackendDevPlan.md)