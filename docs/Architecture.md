# アーキテクチャ

## 設計意図
Gijiroku21は音声を外部に送信しない完全ローカル完結型の議事録アプリとして、プライバシーと常時稼働を両立させることを最優先としています。NPU / CPU / GPU を活用した推論とプレーンなUIを並行して提供し、ITリテラシーが高くない利用者も戸惑わず使えるようにするため、GUIとCoreの責務を明確に分離しています。

## システム構成
```
[ React GUI (Electron) ]
          │
          │ IPC / HTTP (localhost)
          ▼
[ Python Core ]
  ├─ Audio Capture
  ├─ Whisper ONNX Inference
  ├─ Tokenizer
  ├─ Text Post-processing
  └─ Local Storage
```

フロントエンドは`Electron`でラップした`React`アプリケーションで、録音・文字起こし・要約・保存といったUIフローを提供します。Coreと通信する際は`localhost`上の`FastAPI`を介し、軽量なJSON / ストリーミングAPIで音声バッファや文字列をやり取りします。

## フロントエンド（GUI）
- `React` + `TypeScript` でSPAを構成し、`Zustand`やHooksを使った状態管理でリアルタイム表示を高速化。
- 波形やわかりやすいアニメーションで「AIが裏で動いている安心感」を演出。
- 設定画面は最低限の項目に絞り、録音開始操作だけで利用できる導線を確保。

## Core（Python）
- `sounddevice` / `pyaudio` でマイク入力をキャプチャし、バッファリングして`FastAPI`に渡す。
- ONNX Runtime（`Whisper` small 相当）を使用し、NPUを検出した場合は優先的に活用。
- トークナイザーは`HuggingFace`由来のローカルファイルを利用し、FP16 / INT8 モードの準備も可能。
- 結果はローカルストレージにテキストとして出力し、必要に応じて要約と決定事項抽出の前処理を実行。

## AIモデルと推論
- 単一のONNXモデル（encoder + decoder）を読み込み、音声塊ごとに逐次推論。
- 日本語を優先したトークナイズと語彙処理で精度を確保。
- リアルタイム性とCPU負荷のバランスを取り、会議中にもUIで確認可能な応答時間を維持。

## データ・ストレージ
- Documents/Gijiroku21/ 以下に会議フォルダを作成し、`audio.wav`、`transcript.txt`、`summary.md` を保存。
- 設定は`config.json`にまとめ、起動ごとに読み込む。
- すべてのデータはローカルに保持し、アンインストール時も削除されないよう運用。

## 拡張性と将来対応
- モデルの差し替え：core/models/ 配下のONNXファイルを入れ替えるだけで対応可能。
- NPUベンダー別最適化：CPU推論基盤を整えた上で、NPU専用エンジンの後付けが容易。
- 話者分離：別プロセス（pyannote.audio等）での実行を想定し、APIで結果を統合。
- 多言語対応：トークナイザー＆モデル切り替えで段階的に拡張。
- OSサポート拡張：Pythonコア側はOS非依存設計を心がけ、Electronで各OS対応。

## 実装進捗（2025年12月現在）

### 完成度：バックエンド（Core） ~80%
- [x] FastAPI スケルトン、エンドポイント骨格
- [x] Whisper ONNX + tokenizer.json ロード（グリーディデコード実装）
- [x] sounddevice 音声取得 + PCM キュー
- [x] SSE ベース逐次配信
- [x] 会議メタ（meta.json）自動保存
- [ ] テキスト後処理（句読点補完等）- 簡易版のみ
- [ ] 要約生成 - 未実装（将来LLM統合想定）
- [ ] エクスポート（TXT/Markdown）- API骨組みのみ

### 完成度：フロントエンド（React/Electron） ~0%
- [ ] React + Zustand スケルトン
- [ ] ホーム画面・録音UIウィジェット
- [ ] SSE リスナー実装
- [ ] 会議一覧・詳細表示
- [ ] 設定画面

### 次段階の優先課題
1. **Transcript/Summary 保存** (Core側：1～2日)
2. **フロントエンド基本UI** (React側：3～5日)
3. **実オーディオでの統合テスト** (3～5日)
4. **PyInstaller + Electron バンドル** (2～3日)
5. **Windows インストーラー作成** (2～3日)

## 参考資料
- 要件仕様・開発計画: [docs/DevPlan.md](docs/DevPlan.md)
