# MTBBS Linux - Modern BBS System with Database

オリジナルのパソコン通信BBSシステムを現代的な技術で再実装したシステムです。
SQLiteデータベースによる永続化、Web管理UI、カスタマイズ可能なメッセージシステムを搭載しています。

## 🌟 新機能

### システムメッセージカスタマイズ機能 ✨NEW✨

Telnetで表示されるすべてのメニューやメッセージを管理UIから編集できます！

**機能**:
- ✅ **14種類のシステムメッセージをDB管理**
- ✅ **カテゴリ別フィルタ** (Menu/Greeting/Info/Help)
- ✅ **リアルタイム編集** - 編集内容が即座に反映
- ✅ **テンプレート変数対応** - {version}, {user_id}, {handle} などの動的表示
- ✅ **有効/無効切り替え** - メッセージごとに表示制御
- ✅ **起動時自動初期化** - デフォルトメッセージを自動登録

**編集可能なメッセージ**:
- メインメニュー (MAIN_MENU)
- オープニングメッセージ (OPENING_MESSAGE)
- ログイン/ログアウトメッセージ
- ヘルプ画面 (HELP_MESSAGE)
- システム情報 (SYSINFO_MESSAGE, HOST_VERSION)
- 各種サブメニュー (FILE_MENU, READ_MENU, CHAT_MENU, INSTALL_MENU, SYSOP_MENU)
- チャットルーム開始メッセージ
- ファイルボード案内

**アクセス方法**:
```
管理UI (http://localhost:3000) → Messages → メッセージ選択 → Edit → 内容編集 → Save
```

## 特徴

- ✅ **Telnet BBSサーバー**: 伝統的なBBS体験 (Port 23)
- ✅ **SQLiteデータベース**: データ永続化とバックアップ対応
- ✅ **Web管理UI**: モダンなReact + Material-UI
- ✅ **メッセージカスタマイズ**: 全てのテキストをUI上で編集可能
- ✅ **ユーザー管理**: レベル制御、ゲストログイン対応
- ✅ **ボード管理**: 複数掲示板の作成・編集
- ✅ **非同期処理**: Python asyncioによる高速処理

## クイックスタート

### 1. 依存関係インストール

**バックエンド**:
```bash
cd backend
pip install -r requirements.txt
```

**フロントエンド**:
```bash
cd frontend
npm install
```

### 2. データベース初期化

初回起動時に自動的に作成されます:
- `mtbbs.db` ファイル (SQLite)
- テーブル: `users`, `boards`, `messages`, `system_messages`
- デフォルトデータ: システムメッセージ14件

### 3. 起動

**バックエンド** (ターミナル1):
```bash
cd backend
python -m app.main
```

**フロントエンド** (ターミナル2):
```bash
cd frontend
npm run dev
```

### 4. アクセス

- **管理UI**: http://localhost:3000
- **API ドキュメント**: http://localhost:8000/docs
- **Telnet BBS**: `telnet localhost 23`

### 5. 停止

各ターミナルで `Ctrl+C` を押して終了します。

## デフォルトログイン情報

### 初期ユーザー

システムにはデフォルトユーザーは含まれていません。
初回起動後、管理UIから作成するか、ゲストでログインしてください。

### Telnet BBS
- **Guest**: ゲストログイン（パスワード不要）
- **管理UIで作成したユーザー**: 設定したID/パスワードでログイン

## アーキテクチャ

```
┌──────────────────────┐
│  Telnet Client       │  ←→  Telnet BBS Server (Port 23)
│  Web Browser         │  ←→  Frontend (Port 3000)
└──────────────────────┘
          ↓
┌──────────────────────┐
│  FastAPI Backend     │
│  Admin API (8000)    │  ←→  Users, Boards, Messages, Stats
└──────────────────────┘
          ↓
┌──────────────────────┐
│  SQLite Database     │
│  - users             │  ユーザー管理
│  - boards            │  掲示板管理
│  - messages          │  投稿メッセージ
│  - system_messages   │  システムメッセージ (カスタマイズ可能)
└──────────────────────┘
```

## 主な機能

### Telnet BBS機能
- ✅ ユーザー認証 (ID/パスワード、ゲストログイン)
- ✅ メッセージボード (複数ボード対応)
- ✅ メッセージ投稿/閲覧/削除
- ✅ 新着メッセージ確認
- ✅ ユーザーレベル制御 (0-9)
- ✅ カスタマイズ可能なメニュー表示

### Web管理UI機能
- ✅ **ダッシュボード** - システム統計情報
- ✅ **ユーザー管理** - 作成/削除/一覧表示
- ✅ **ボード管理** - 掲示板の作成/編集/削除
- ✅ **メッセージ管理** ✨NEW✨ - システムメッセージのカスタマイズ
  - カテゴリフィルタ (Menu/Greeting/Info/Help)
  - リアルタイム編集ダイアログ
  - テンプレート変数サポート
  - 有効/無効切り替え
  - デフォルトメッセージ初期化
- ✅ **接続監視** - Telnet接続のリアルタイム表示
- ✅ **設定管理** - システム設定

### システム管理
- ✅ REST API (FastAPI)
- ✅ SQLAlchemy ORM (非同期)
- ✅ 自動マイグレーション
- ✅ セッション管理

## Telnetコマンド

```
[N]ews   - 新着記事を読む
[R]ead   - メッセージボードを読む
[E]nter  - メッセージを書き込む
[M]ail   - メールを読む (未実装)
[H]elp   - ヘルプ表示
[U]sers  - ユーザーリスト
[W]ho    - ログイン中のユーザー
[Y]sysinfo - システム情報
[_]      - バージョン表示
[#]      - ステータス表示
[Q]uit   - ログアウト
```

## 技術スタック

### Backend
- **Python 3.11+**
- **FastAPI** - 高速Web APIフレームワーク
- **SQLAlchemy 2.0** - 非同期ORM
- **aiosqlite** - 非同期SQLiteドライバ
- **Pydantic** - データバリデーション
- **passlib** - パスワードハッシュ化 (bcrypt)
- **asyncio** - 非同期I/O処理

### Frontend
- **React 18** + TypeScript
- **Material-UI (MUI) v5** - UIコンポーネント
- **React Query** - データフェッチング/キャッシング
- **Vite** - 高速ビルドツール
- **Axios** - HTTPクライアント

### Database
- **SQLite** - 軽量で移植性の高いデータベース
- **自動マイグレーション** - テーブル自動作成
- **外部キー制約** - データ整合性保証

## ディレクトリ構造

```
mtbbs-linux/
├── backend/
│   ├── app/
│   │   ├── models/
│   │   │   ├── user.py              # ユーザーモデル
│   │   │   ├── board.py             # ボード/メッセージモデル
│   │   │   └── system_message.py   # システムメッセージモデル ✨NEW✨
│   │   ├── services/
│   │   │   ├── user_service.py      # ユーザー管理ロジック
│   │   │   ├── board_service.py     # ボード管理ロジック
│   │   │   └── message_service.py   # メッセージ管理ロジック ✨NEW✨
│   │   ├── api/
│   │   │   ├── admin.py             # 管理API (Users, Boards, Messages)
│   │   │   └── bbs.py               # BBS API
│   │   ├── protocols/
│   │   │   ├── telnet_server.py     # Telnetサーバー
│   │   │   └── telnet_handler.py    # セッション管理
│   │   ├── resources/
│   │   │   └── messages_ja.py       # デフォルトメッセージ定義
│   │   ├── core/
│   │   │   ├── config.py            # 設定管理
│   │   │   └── database.py          # DB接続管理
│   │   └── main.py                  # アプリケーションエントリポイント
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── pages/
│   │   │   ├── Dashboard.tsx
│   │   │   ├── Users.tsx
│   │   │   ├── Boards.tsx
│   │   │   ├── Messages.tsx         # メッセージ管理UI ✨NEW✨
│   │   │   ├── Connections.tsx
│   │   │   └── Settings.tsx
│   │   ├── components/
│   │   │   └── Layout.tsx
│   │   ├── api/
│   │   │   └── client.ts            # API クライアント
│   │   ├── App.tsx
│   │   └── main.tsx
│   └── package.json
├── mtbbs.db                         # SQLite データベース (自動生成)
└── README.md
```

## API エンドポイント

### 管理API (`/api/admin`)

#### ユーザー管理
- `GET /api/admin/users` - ユーザー一覧
- `GET /api/admin/users/{user_id}` - ユーザー詳細
- `POST /api/admin/users` - ユーザー作成
- `DELETE /api/admin/users/{user_id}` - ユーザー削除

#### ボード管理
- `GET /api/admin/boards` - ボード一覧
- `GET /api/admin/boards/{board_id}` - ボード詳細
- `POST /api/admin/boards` - ボード作成
- `DELETE /api/admin/boards/{board_id}` - ボード削除

#### メッセージ管理 ✨NEW✨
- `GET /api/admin/messages` - システムメッセージ一覧
- `GET /api/admin/messages?category={category}` - カテゴリフィルタ
- `GET /api/admin/messages/{message_key}` - メッセージ詳細
- `PUT /api/admin/messages/{message_key}` - メッセージ更新
- `POST /api/admin/messages/initialize` - デフォルトメッセージ初期化

#### システム統計
- `GET /api/admin/stats` - システム統計情報
- `GET /api/admin/connections` - アクティブ接続一覧

### BBS API (`/api/bbs`)
- `GET /api/bbs/boards` - ボード一覧
- `GET /api/bbs/boards/{board_id}/messages` - メッセージ一覧
- `GET /api/bbs/boards/{board_id}/messages/{message_no}` - メッセージ詳細
- `POST /api/bbs/messages` - メッセージ投稿

## トラブルシューティング

### データベースリセット
```bash
rm mtbbs.db
python -m app.main  # 自動的に再作成・初期化
```

### メッセージが表示されない場合
1. 管理UI → Messages で該当メッセージが `Active` になっているか確認
2. "Initialize Defaults" ボタンでデフォルトメッセージを再登録
3. Telnetを再接続して確認

### ポートが使用中の場合
```bash
# ポート確認
netstat -an | grep 23
netstat -an | grep 8000
netstat -an | grep 3000

# プロセス強制終了 (Linux/Mac)
lsof -ti:23 | xargs kill
lsof -ti:8000 | xargs kill
lsof -ti:3000 | xargs kill
```

### Frontend ビルドエラー
```bash
cd frontend
rm -rf node_modules package-lock.json
npm install
```

### Telnet接続エラー
- **Windowsの場合**: Telnetクライアントを有効化
  ```cmd
  dism /online /Enable-Feature /FeatureName:TelnetClient
  ```

### 依存関係のエラー
```bash
# バックエンド
cd backend
pip install --upgrade pip
pip install -r requirements.txt

# フロントエンド
cd frontend
npm install
```

## 開発情報

### 環境変数 (.env)
```env
# Database
DATABASE_URL=sqlite+aiosqlite:///./mtbbs.db

# Server
HOST=0.0.0.0
PORT=8000
DEBUG=True

# Telnet
TELNET_HOST=0.0.0.0
TELNET_PORT=23
TELNET_MAX_CONNECTIONS=100
TELNET_IDLE_TIMEOUT=1800

# Security
SECRET_KEY=your-secret-key-change-this-in-production
```

### ログ確認
```bash
# バックエンド起動ログ
python -m app.main

# データベース確認
sqlite3 mtbbs.db
.tables
SELECT * FROM system_messages;
.quit
```

### API ドキュメント
起動後、以下のURLでインタラクティブAPIドキュメントにアクセスできます:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## システム要件

- **Python**: 3.11以上
- **Node.js**: 16以上
- **OS**: Windows, macOS, Linux
- **メモリ**: 最小 1GB
- **ディスク**: 最小 100MB

## セキュリティ

### 現在の実装
- ✅ パスワードハッシュ化 (bcrypt)
- ✅ SQLインジェクション対策 (ORM使用)
- ✅ CORS設定
- ✅ セッション管理

### 本番環境での推奨事項
- [ ] HTTPS/TLS対応
- [ ] JWT認証 (現在未実装)
- [ ] レート制限
- [ ] IPアドレス制限
- [ ] セキュリティヘッダー設定

## 今後の開発予定

### 機能拡張
- [ ] メール機能の実装
- [ ] メッセージ返信機能 (スレッド化)
- [ ] ファイルアップロード/ダウンロード
- [ ] リアルタイムチャット
- [ ] 全文検索機能
- [ ] ユーザープロフィール編集

### パフォーマンス最適化
- [ ] Redis キャッシング
- [ ] WebSocket化 (リアルタイム更新)
- [ ] データベースインデックス最適化
- [ ] 画像最適化

### 管理機能強化
- [ ] ログビューア
- [ ] バックアップ/リストア機能
- [ ] ユーザーアクティビティログ
- [ ] システム設定UI

## バージョン情報

- **Version**: 4.1.0
- **Last Updated**: 2025-12-21
- **Original MTBBS**: Yoshihiro Myokan (MYO) - 1997-1999
- **Modern Implementation**: 2024-2025

## 変更履歴

### v4.1.0 (2025-12-21) ✨NEW✨
- システムメッセージカスタマイズ機能追加
- データベースでメッセージ管理
- 管理UIからのリアルタイム編集
- SQLite完全対応（PostgreSQL依存削除）
- 不要な依存関係削除（Redis, JWT）

### v4.0.0 (2024-2025)
- SQLiteデータベース統合
- React管理UI実装
- FastAPI移行
- 非同期処理対応

## ライセンス

本プロジェクトはオリジナルのMTBBSのコンセプトを継承し、現代的な技術で再実装したものです。

## 貢献

機能追加、バグ修正、ドキュメント改善などのPull Requestを歓迎します!

### 開発ガイドライン
1. コードは既存のスタイルに従ってください
2. 新機能には適切なコメントを追加してください
3. APIの変更はドキュメントも更新してください
4. コミットメッセージは明確に記述してください

## サポート

問題や質問がある場合は、GitHubのIssuesで報告してください。

---

**Made with ❤️ by Claude + Human Collaboration**
