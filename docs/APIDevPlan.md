# Gijiroku21

## バックエンド API 仕様書

**Version 1.0**

---

## 1. 基本仕様

### 1.1 通信方式

* プロトコル：HTTP
* ホスト：`localhost`
* ポート：`127.0.0.1:8765`（例）
* データ形式：JSON
* 文字コード：UTF-8

---

### 1.2 API 設計方針

* ステートレス（会議状態は Core 側で管理）
* UI は「命令」と「状態取得」のみ行う
* 音声データは API 経由で送らない

---

### 1.3 共通レスポンス構造

```json
{
  "success": true,
  "data": {},
  "error": null
}
```

エラー時：

```json
{
  "success": false,
  "data": null,
  "error": {
    "code": "ERROR_CODE",
    "message": "Human readable message"
  }
}
```

---

## 2. 状態管理 API

---

### 2.1 AI / Core 状態取得

**GET** `/status`

#### 説明

* Core 全体の状態を取得
* UI の「安心感表示」に使用

#### Response

```json
{
  "success": true,
  "data": {
    "ai_state": "ready",
    "recording": false,
    "model": "whisper-small",
    "device": "NPU",
    "uptime_sec": 123
  },
  "error": null
}
```

#### ai_state 値

* `initializing`
* `ready`
* `listening`
* `processing`
* `error`

---

## 3. 録音制御 API

---

### 3.1 録音開始

**POST** `/record/start`

#### Request

```json
{
  "meeting_title": "Weekly Meeting",
  "language": "ja",
  "save_audio": true
}
```

| フィールド         | 型       | 必須 | 説明       |
| ------------- | ------- | -- | -------- |
| meeting_title | string  | ○  | 会議名      |
| language      | string  | ×  | 省略時 `ja` |
| save_audio    | boolean | ×  | WAV保存有無  |

#### Response

```json
{
  "success": true,
  "data": {
    "meeting_id": "2025-01-23-001"
  },
  "error": null
}
```

---

### 3.2 録音停止

**POST** `/record/stop`

#### Response

```json
{
  "success": true,
  "data": {
    "duration_sec": 3560
  },
  "error": null
}
```

---

## 4. リアルタイム文字起こし API

---

### 4.1 文字起こしストリーム取得

**GET** `/transcript/stream`

> ※ 実装は **Server-Sent Events（SSE）** または **WebSocket** を想定
> 初期実装では SSE 推奨

#### SSE イベント形式

```json
{
  "type": "partial",
  "text": "本日の会議では"
}
```

```json
{
  "type": "final",
  "text": "本日の会議では新しい提案について議論します。"
}
```

| type    | 説明      |
| ------- | ------- |
| partial | 暫定文字起こし |
| final   | 確定文字起こし |
| status  | 状態通知    |

---

## 5. 会議データ取得 API

---

### 5.1 会議一覧取得

**GET** `/meetings`

#### Response

```json
{
  "success": true,
  "data": [
    {
      "meeting_id": "2025-01-23-001",
      "title": "Weekly Meeting",
      "date": "2025-01-23",
      "duration_sec": 3560
    }
  ],
  "error": null
}
```

---

### 5.2 会議詳細取得

**GET** `/meetings/{meeting_id}`

#### Response

```json
{
  "success": true,
  "data": {
    "meeting_id": "2025-01-23-001",
    "title": "Weekly Meeting",
    "transcript": "......全文......",
    "summary": [
      "提案Aについて議論",
      "次回までに資料作成"
    ]
  },
  "error": null
}
```

---

## 6. エクスポート API

---

### 6.1 エクスポート実行

**POST** `/export`

#### Request

```json
{
  "meeting_id": "2025-01-23-001",
  "format": "txt"
}
```

| format | 値        |
| ------ | -------- |
| txt    | プレーンテキスト |
| md     | Markdown |

#### Response

```json
{
  "success": true,
  "data": {
    "file_path": "Documents/Gijiroku21/meetings/2025-01-23/transcript.txt"
  },
  "error": null
}
```

---

## 7. 設定 API

---

### 7.1 設定取得

**GET** `/config`

#### Response

```json
{
  "success": true,
  "data": {
    "language": "ja",
    "model": "small",
    "save_audio": true
  },
  "error": null
}
```

---

### 7.2 設定更新

**POST** `/config`

#### Request

```json
{
  "language": "ja",
  "model": "small"
}
```

---

## 8. エラーコード一覧（例）

| code                  | 意味       |
| --------------------- | -------- |
| MIC_NOT_FOUND         | マイク未検出   |
| MODEL_LOAD_FAILED     | モデルロード失敗 |
| RECORDING_IN_PROGRESS | 録音中      |
| INTERNAL_ERROR        | 内部エラー    |

---

## 9. セキュリティ・制約

* localhost 限定
* 認証不要（ローカル前提）
* 外部アクセス不可

---

## 10. API 成功条件

* UI が状態を常に把握できる
* 例外時も UI が落ちない
* 長時間会議で API が詰まらない

---

## 付記（設計思想）

この API は
**「UI は迷わない／Core は黙々と処理する」**
という UX 心理設計に基づいている。