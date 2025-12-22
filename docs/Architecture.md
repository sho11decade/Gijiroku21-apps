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

## 参考資料
## 参考資料
- 要件仕様・開発計画: [docs/DevPlan.md](docs/DevPlan.md)
