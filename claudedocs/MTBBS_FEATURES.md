# MTBBS (Multi-Task Bulletin Board System) 機能ドキュメント

## 概要
MTBBSは、オリジナルのパソコン通信BBSシステムをモダンな技術で再実装したシステムです。
Telnetプロトコルを使用した伝統的なBBS機能と、現代的なWeb管理UIを組み合わせています。

## システムアーキテクチャ

### コンポーネント構成
```
┌─────────────────────────────────────────────────┐
│  クライアント層                                   │
├─────────────────────────────────────────────────┤
│  - Telnetクライアント (端末エミュレータ)          │
│  - Webブラウザ (管理UI)                          │
└─────────────────────────────────────────────────┘
           ↓                    ↓
┌─────────────────────────────────────────────────┐
│  アプリケーション層                               │
├─────────────────────────────────────────────────┤
│  - Telnet BBSサーバー (demo_server.py)          │
│  - Admin API (simple_api.py)                    │
│  - Telnet Monitor API (telnet_monitor.py)       │
│  - Frontend Server (React + Vite)               │
└─────────────────────────────────────────────────┘
           ↓                    ↓
┌─────────────────────────────────────────────────┐
│  データ層                                        │
├─────────────────────────────────────────────────┤
│  - インメモリDB (users_db, boards_db)           │
│  - 接続情報 (telnet_connections.json)           │
└─────────────────────────────────────────────────┘
```

---

## 1. Telnet BBS機能

### 1.1 接続とログイン

#### 接続方法
```bash
telnet localhost 2323
```

#### ログイン方式
- **一般ユーザーログイン**: User ID + Password
- **ゲストログイン**: "guest"と入力するだけで接続可能

#### デフォルトアカウント
| User ID | Password | Handle Name | Level |
|---------|----------|-------------|-------|
| admin   | admin123 | Administrator | 9   |
| test    | test123  | TestUser    | 1     |
| guest   | (なし)    | Guest       | 0     |

### 1.2 メインメニュー

```
MTBBS Demo - Main Menu   HH:MM  user_id / handle_name
BOARD/MAIL -------------  INFORMATION ------------  OTHERS -----------------
[R]ead  メッセージを読む| [H]elp    ヘルプ        | [Q]uit    ログアウト
[E]nter メッセージ書込  | [W]ho     ログイン中    | [#]       ステータス
```

#### コマンド一覧
| コマンド | 機能 | 説明 |
|---------|------|------|
| **R** | Read | ボード一覧表示とメッセージ閲覧 |
| **E** | Enter | メッセージ投稿 |
| **W** | Who | 現在ログイン中のユーザー一覧 |
| **H** | Help | ヘルプ表示 |
| **#** | Status | 自分のステータス情報表示 |
| **Q** | Quit | ログアウト |

### 1.3 ボード機能

#### ボード構造
```python
{
    "board_id": int,      # ボードID
    "name": str,          # ボード名
    "description": str,   # 説明
    "read_level": int,    # 読み取り権限レベル (0-9)
    "write_level": int,   # 書き込み権限レベル (0-9)
    "is_active": bool,    # アクティブ状態
    "messages": []        # メッセージリスト
}
```

#### デフォルトボード
1. **General** - 一般ディスカッション
2. **Announcements** - システムアナウンス

### 1.4 メッセージ機能

#### メッセージ投稿フロー
```
1. Enterコマンド実行
2. ボード番号入力
3. タイトル入力
4. 本文入力 (複数行可能、「.」だけの行で終了)
5. 投稿完了
```

#### メッセージ構造
```python
{
    "title": str,         # タイトル
    "body": str,          # 本文
    "handle": str,        # 投稿者ハンドル名
    "user_id": str,       # 投稿者ID
    "date": datetime      # 投稿日時
}
```

### 1.5 ユーザーレベルシステム

#### レベル定義
| Level | 名称 | 権限 |
|-------|------|------|
| 0 | Guest | 読み取りのみ (制限あり) |
| 1 | User | 一般投稿可能 |
| 2-4 | Advanced User | 拡張権限 |
| 5-8 | Moderator | モデレーター権限 |
| 9 | Administrator | 全権限 |

---

## 2. Web管理UI機能

### 2.1 ダッシュボード
- システム統計情報の表示
- アクティブユーザー数
- 総ユーザー数
- ボード数
- メッセージ総数
- Telnet接続数

### 2.2 ユーザー管理

#### 機能一覧
- ユーザー一覧表示
- ユーザー作成
- ユーザー削除
- ユーザー情報編集

#### ユーザー属性
```typescript
{
  user_id: string        // ユーザーID (一意)
  handle_name: string    // ハンドル名 (表示名)
  email: string          // メールアドレス
  level: number          // ユーザーレベル (0-9)
  last_login: datetime   // 最終ログイン日時
  created_at: datetime   // アカウント作成日時
}
```

### 2.3 ボード管理

#### 機能一覧
- ボード一覧表示
- **ボード作成** (実装済み)
- **ボード編集** (実装済み)
- **ボード削除** (実装済み) ✨NEW✨

#### ボード設定項目
- Board ID (ボードID)
- Board Name (ボード名)
- Description (説明)
- Read Level (読み取り権限レベル: 0-9)
- Write Level (書き込み権限レベル: 0-9)
- Active Status (アクティブ/非アクティブ)

### 2.4 Telnetモニタリング ✨NEW✨

#### 統計情報カード
- **総接続数**: 現在アクティブな接続の総数
- **認証済みユーザー**: ログイン完了したユーザー数
- **ゲストユーザー**: ゲストログイン中のユーザー数

#### 接続一覧テーブル
| 列 | 情報 |
|----|------|
| クライアントID | IPアドレス:ポート |
| ユーザーID | ログインユーザーID |
| ハンドル名 | 表示名 |
| レベル | ユーザーレベル |
| 認証状態 | 認証済み/未認証 |
| 接続時刻 | 接続開始時刻 |

#### リアルタイム更新
- 3秒ごとに自動更新
- 接続/切断を即座に反映

---

## 3. API仕様

### 3.1 Admin API (Port 8000)

#### ユーザー管理
```
GET    /api/admin/users           # ユーザー一覧
GET    /api/admin/users/{user_id} # ユーザー詳細
POST   /api/admin/users           # ユーザー作成
DELETE /api/admin/users/{user_id} # ユーザー削除
```

#### ボード管理
```
GET    /api/admin/boards            # ボード一覧
GET    /api/admin/boards/{board_id} # ボード詳細
POST   /api/admin/boards            # ボード作成
DELETE /api/admin/boards/{board_id} # ボード削除 ✨NEW✨
```

#### システム情報
```
GET /api/admin/stats       # 統計情報
GET /api/admin/connections # 接続情報
```

### 3.2 Telnet Monitor API (Port 8001) ✨NEW✨

```
GET /api/telnet/connections  # 現在のTelnet接続一覧
GET /api/telnet/stats        # Telnet接続統計情報
```

#### 接続情報レスポンス
```json
{
  "connections": [
    {
      "client_id": "127.0.0.1:12345",
      "user_id": "admin",
      "handle_name": "Administrator",
      "level": 9,
      "authenticated": true,
      "connected_at": "2025-12-21T10:30:00"
    }
  ],
  "total": 1,
  "last_updated": "2025-12-21T10:30:05"
}
```

#### 統計情報レスポンス
```json
{
  "total_connections": 5,
  "authenticated_users": 3,
  "guest_users": 2,
  "level_distribution": {
    "0": 2,
    "1": 1,
    "9": 2
  },
  "last_updated": "2025-12-21T10:30:05"
}
```

---

## 4. セキュリティとアクセス制御

### 4.1 認証システム
- **Telnet認証**: User ID + Password (平文 - デモ用)
- **ゲストアクセス**: パスワード不要

### 4.2 アクセスレベル制御
- ボード単位で読み取り/書き込みレベルを設定可能
- ユーザーレベルがボードの要求レベル以上で許可

### 4.3 CORS設定
- Web UI用に全オリジン許可設定 (開発環境用)

---

## 5. 技術スタック

### バックエンド
- **Python 3.x**
  - FastAPI (Web API Framework)
  - Uvicorn (ASGI Server)
  - asyncio (非同期IO)

### フロントエンド
- **React 18** (TypeScript)
- **Material-UI (MUI)** (UIコンポーネント)
- **React Query** (データフェッチング)
- **React Router** (ルーティング)
- **Vite** (ビルドツール)

### プロトコル
- **Telnet** (BBS接続)
- **HTTP/REST** (Web API)
- **WebSocket** (将来的なリアルタイム通信用)

---

## 6. ファイル構造

```
mtbbs-linux/
├── demo_server.py              # Telnet BBSサーバー
├── simple_api.py               # Admin API
├── telnet_monitor.py           # Telnet Monitor API ✨NEW✨
├── test_telnet.py              # Telnet接続テスト
├── start.sh                    # 起動スクリプト ✨NEW✨
├── stop.sh                     # 停止スクリプト ✨NEW✨
├── install.sh                  # インストールスクリプト ✨NEW✨
├── telnet_connections.json     # Telnet接続情報 (自動生成)
├── logs/                       # ログディレクトリ
│   ├── api.log
│   ├── telnet.log
│   └── frontend.log
├── .pids/                      # PIDファイル (自動生成)
│   ├── api.pid
│   ├── telnet.pid
│   └── frontend.pid
├── frontend/                   # React フロントエンド
│   ├── src/
│   │   ├── pages/
│   │   │   ├── Dashboard.tsx   # ダッシュボード
│   │   │   ├── Users.tsx       # ユーザー管理
│   │   │   ├── Boards.tsx      # ボード管理
│   │   │   ├── Connections.tsx # Telnet接続監視 (改善版)
│   │   │   └── Settings.tsx    # 設定
│   │   ├── api/
│   │   │   └── client.ts       # API クライアント
│   │   └── components/
│   │       └── Layout.tsx      # レイアウト
│   ├── package.json
│   └── vite.config.ts
└── claudedocs/                 # ドキュメント
    └── MTBBS_FEATURES.md       # 本ドキュメント
```

---

## 7. 起動方法

### 初回セットアップ
```bash
chmod +x install.sh start.sh stop.sh
./install.sh
```

### サービス起動
```bash
./start.sh
```

起動後、以下のサービスが利用可能:
- **Backend API**: http://localhost:8000
- **Telnet Monitor API**: http://localhost:8001
- **Frontend UI**: http://localhost:5173
- **Telnet BBS**: telnet localhost 2323

### サービス停止
```bash
./stop.sh
```

---

## 8. 実装された新機能 ✨

### ボード削除機能
- **フロントエンド**: 削除ボタン追加、確認ダイアログ
- **バックエンド**: DELETE /api/admin/boards/{board_id} エンドポイント
- **API Client**: deleteBoard() メソッド追加

### Telnetモニタリング機能
- **リアルタイム接続監視**: 3秒ごとの自動更新
- **統計ダッシュボード**: 総接続数、認証済み、ゲストユーザー数
- **詳細接続一覧**: クライアントID、ユーザー情報、レベル、認証状態
- **JSON データエクスポート**: demo_server.pyが接続情報をJSON出力
- **専用Monitor API**: telnet_monitor.py で統計情報提供

### システム管理スクリプト
- **start.sh**: 全サービスの一括起動
- **stop.sh**: 全サービスの一括停止
- **install.sh**: 依存関係の一括インストール/更新

---

## 9. 今後の拡張可能性

### 機能拡張案
- [ ] データベース統合 (SQLite/PostgreSQL)
- [ ] メッセージ返信機能 (スレッド化)
- [ ] メール機能 (ユーザー間メッセージング)
- [ ] ファイルアップロード/ダウンロード
- [ ] チャット機能 (リアルタイム)
- [ ] 全文検索機能
- [ ] ログ閲覧機能
- [ ] システム設定UI

### セキュリティ強化案
- [ ] パスワードハッシュ化 (bcrypt)
- [ ] JWT認証
- [ ] レート制限
- [ ] IPアドレス制限
- [ ] セッション管理

### パフォーマンス最適化案
- [ ] Redis キャッシング
- [ ] WebSocket化 (監視機能)
- [ ] データベースインデックス最適化
- [ ] CDN統合

---

## 10. 開発者向け情報

### 環境要件
- Python 3.8+
- Node.js 16+
- npm 8+

### 開発モード
```bash
# バックエンド開発
python3 demo_server.py      # Telnet BBS
python3 simple_api.py       # Admin API
python3 telnet_monitor.py   # Monitor API

# フロントエンド開発
cd frontend
npm run dev
```

### テスト
```bash
# Telnet接続テスト
python3 test_telnet.py

# API テスト
curl http://localhost:8000/api/admin/stats
curl http://localhost:8001/api/telnet/connections
```

---

## 11. トラブルシューティング

### Telnet接続エラー
```bash
# ポート2323が使用中かチェック
netstat -an | grep 2323

# プロセス強制終了
pkill -f demo_server.py
```

### Frontend ビルドエラー
```bash
cd frontend
rm -rf node_modules package-lock.json
npm install
```

### API接続エラー
- CORSエラー: simple_api.pyのCORS設定確認
- 接続拒否: バックエンドサービスが起動しているか確認

---

## 12. ライセンスと著作権

本システムは、オリジナルのMTBBS (Multi-Task Bulletin Board System)の
コンセプトを継承し、現代的な技術で再実装したものです。

**開発者**: Claude + Human Collaboration
**バージョン**: 4.0.0
**最終更新**: 2025-12-21

---

## 付録A: コマンドリファレンス

### Telnet BBSコマンド
```
R - Read    メッセージ閲覧
E - Enter   メッセージ投稿
W - Who     ログイン中ユーザー
H - Help    ヘルプ表示
# - Status  自分のステータス
Q - Quit    ログアウト
```

### 管理スクリプト
```bash
./install.sh  # 初回セットアップ
./start.sh    # サービス起動
./stop.sh     # サービス停止
```

### APIエンドポイント
```
GET    /api/admin/users
POST   /api/admin/users
DELETE /api/admin/users/{user_id}
GET    /api/admin/boards
POST   /api/admin/boards
DELETE /api/admin/boards/{board_id}
GET    /api/admin/stats
GET    /api/telnet/connections
GET    /api/telnet/stats
```

---

**ドキュメント終わり**
