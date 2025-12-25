# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

## [Unreleased]

## [0.1α] - 2025-12-25 - Security Enhancement & Phase 1-2 Features

### Added

#### 🛡️ Step 1: Security Enhancement & Backup Automation
- **Rate Limiting System** (`backend/app/utils/rate_limiter.py`)
  - Brute-force attack prevention (3 attempts/60 seconds per IP)
  - Automatic cleanup of expired entries
  - Thread-safe implementation

- **Input Sanitization** (`backend/app/utils/input_sanitizer.py`)
  - XSS and SQL injection prevention
  - User ID, email, message sanitization
  - Pattern-based detection for malicious inputs

- **System Monitoring** (`backend/app/utils/monitor.py`)
  - Real-time health checks (database, disk, memory, sessions)
  - Metrics collection
  - Integration with SYSOP statistics menu

- **Automated Database Backup** (`scripts/backup_database.sh`)
  - SQLite `.backup` command for consistent backups
  - Integrity verification
  - 7-day retention policy
  - Automated cleanup

- **Health Check Script** (`scripts/health_check.py`)
  - Standalone health check for monitoring tools
  - Exit codes: 0=OK, 1=WARNING, 2=CRITICAL, 3=ERROR

#### 📧 Step 2: Mail System
- **Mail Table** (`backend/app/models/mail.py`, `backend/app/services/mail_service.py`)
  - User-to-user messaging system
  - Soft delete (two-phase deletion)
  - Mail reply functionality with "Re:" prefix
  - Inbox/Sent box separation
  - Unread message count

- **Mail Commands** (`M` command in Telnet)
  - `M → R`: Read inbox
  - `M → S`: Send mail
  - `M → T`: View sent mail
  - Reply and delete functions

#### 👤 Step 2: User Management Features
- **User Registration** (`A` command)
  - Self-registration system
  - User ID validation (4-8 chars, alphanumeric)
  - Password confirmation and bcrypt hashing
  - Email validation (optional)
  - Rate limiting integration

- **Profile Management** (`I` command - Install Menu)
  - `I → P`: Change password
  - `I → H`: Change handle name
  - `I → M`: Edit profile memo (multi-line)
  - `I → E`: Change email

- **Profile Viewing** (`O` command)
  - Display user information
  - Show level, email, created date, last login
  - Profile memo display

- **Who's Online Enhancement** (`W` command)
  - Show all connected users (not just self)
  - Display handle, user ID, connection time
  - Current user indicator

#### 🔧 Step 3: SYSOP Management System
- **SYSOP Menu** (`@` command - Level 9 required)
  - `@ → U`: User management (list all users with stats)
  - `@ → L`: Change user level (0-9 with confirmation)
  - `@ → B`: Board management (edit read/write levels, enforced news)
  - `@ → S`: System statistics (users, boards, health status)
  - `@ → K`: Kick user (disconnect online users)

#### 📖 Step 3: Read Board Submenu
- **Read Submenu** (`R` → Board → Submenu)
  - `R → R`: Sequential read (read unread messages in order)
  - `R → I`: Individual select (choose message by number)
  - `R → S`: Search (keyword search in title/body)
  - `R → L`: List all messages
  - `R → Q`: Quit to main menu

- **Auto-read Mode** (`R0@` command)
  - Bypass submenu and read all messages automatically
  - Compatible with continuous command syntax

### Changed

#### Backend
- `backend/app/protocols/telnet_handler.py`
  - Added ~1,850 lines for new features
  - Integrated rate limiting in login flow
  - Input sanitization throughout
  - SYSOP menu implementation (330 lines)
  - Read board submenu implementation (238 lines)
  - Mail system implementation (320 lines)
  - User registration (120 lines)
  - Profile management (200 lines)

- `backend/app/protocols/telnet_server.py`
  - Integrated monitoring system
  - Health check task (5-minute intervals)
  - Metrics collection task (10-minute intervals)

- `backend/app/services/user_service.py`
  - Added `is_user_id_available()` method
  - Enhanced user creation with reactivation support

- `backend/app/services/board_service.py`
  - Enhanced `update_board()` with enforced_news parameter
  - Search functionality for messages

### Database

#### New Tables
- `mail` - User-to-user messaging
  - Fields: mail_id, sender_id, recipient_id, subject, body, sent_at, read_at, is_read, is_deleted_by_sender, is_deleted_by_recipient
  - Indexes: recipient, sender, sent_at

### Migration
- `backend/scripts/migrate_add_mail_table.py`
  - Creates mail table with proper indexes
  - Automatic verification

### Documentation
- `claudedocs/STEP1-3_IMPLEMENTATION_GUIDE.md` (~1,400 lines)
  - Comprehensive implementation documentation
  - Feature descriptions with code examples
  - Testing checklist
  - Troubleshooting guide
  - Performance optimization tips
  - Future enhancement roadmap

### Statistics
- **Total new files**: 10
- **Total new code**: ~3,500 lines
- **Modified files**: 3
- **Total features**: 23
- **Compatibility improvement**: 31% → 65% (mtbbs302 command coverage)

### Security Improvements
- Rate limiting (brute-force prevention)
- Input sanitization (XSS/SQL injection prevention)
- Password hashing (bcrypt with automatic salt)
- Access control (level-based permissions)
- Audit logging (user actions tracked)

### Copyright
- **Original MTBBS Ver 3.02**: Copyright (C) 1997.10.9 By Yoshihiro Myokan
- **MTBBS-Linux**: Copyright (C) 2025 kuchan

---

## [2025-12-23] - i18n対応と連続コマンド実行機能

### Added

#### 🌐 国際化対応 (i18n)
- **日本語/英語切り替え機能**
  - `frontend/src/i18n.ts` - i18next設定ファイル
  - `frontend/src/locales/ja.json` - 日本語翻訳ファイル
  - `frontend/src/locales/en.json` - 英語翻訳ファイル
  - `frontend/src/components/LanguageSwitcher.tsx` - 言語切り替えコンポーネント
  - LocalStorageに言語設定を保存し、次回訪問時も保持
  - 管理UI全画面で日本語/英語対応

#### 📡 Telnet連続コマンド実行機能
- **コマンドライン処理の実装** (`backend/app/protocols/telnet_handler.py`)
  - `N@` - ニュース自動読み込み
  - `R0` - 掲示板0番に直接アクセス
  - `R0@` - 掲示板0番を自動読み込み
  - `E0` - 掲示板0番に直接投稿
  - 元のMTBBS（Delphi版）のコマンド体系に準拠
  - `command_line` インスタンス変数で連続コマンドを管理

#### 🗄️ データベース管理機能
- **初期化機能** (`backend/app/api/admin.py`)
  - `/admin/database/initialize` エンドポイント追加
  - 全データ削除→デフォルトデータ作成を一括実行
  - sysopユーザー、infoボードを自動作成
  - 管理UIに初期化ボタン追加 (`frontend/src/pages/Settings.tsx`)
  - 確認ダイアログとトースト通知でUX向上

#### 👥 ユーザー管理機能強化
- **ユーザーフラグ追加** (`backend/app/models/user.py`)
  - `is_active` - アカウントの有効/無効切り替え
  - `must_change_password_on_next_login` - 次回ログイン時のパスワード変更強制
  - ユーザーサービスとAPI連携 (`backend/app/services/user_service.py`)

#### 📋 掲示板機能強化
- **掲示板サービス拡張** (`backend/app/services/board_service.py`)
  - `get_board_by_id()` - ID指定での掲示板取得
  - 連続コマンド実行をサポート

#### 🧪 テスト・開発ツール
- **動作確認スクリプト** (`test_commands.py`)
  - 対話式Telnetテストツール
  - 基本コマンド、連続コマンド、ニュース、掲示板、投稿のテストモード
  - 自動ログイン機能

### Changed

#### Frontend
- `frontend/src/main.tsx` - i18n設定をインポート
- `frontend/src/components/Layout.tsx` - 言語切り替えボタン追加、メニュー項目を翻訳対応
- `frontend/src/pages/Settings.tsx` - 全UI要素をi18n対応、DB初期化機能追加
- `frontend/src/pages/Users.tsx` - ユーザーフラグ対応、状態管理修正
- `frontend/src/pages/Boards.tsx` - 掲示板管理UI改善
- `frontend/package.json` - i18next関連パッケージ追加

#### Backend
- `backend/app/protocols/telnet_handler.py` - コマンド解析ロジック全面改修
  - 連続コマンド対応のため`main_loop()`修正
  - `news()`, `read_board()`, `enter_message()`メソッド拡張
- `backend/app/services/user_service.py` - ユーザーフラグ対応
- `backend/app/api/admin.py` - DB初期化エンドポイント追加

### Removed

#### クリーンアップ
- `demo_server.py` - デモ用サーバー削除
- `simple_api.py` - シンプルAPI削除
- `telnet_monitor.py` - Telnetモニター削除
- `test_telnet.py` - 旧テストファイル削除

### Technical Details

#### Dependencies
- `i18next: ^23.7.6` - 国際化フレームワーク
- `react-i18next: ^13.5.0` - React統合

#### File Statistics
- **23 files changed**
- **+1,259 insertions**
- **-664 deletions**

#### Commit
- Hash: `96c8293`
- Date: 2025-12-23 21:50:54
- Branch: main

---

## 機能の使い方

### i18n（言語切り替え）
1. 管理UI（http://localhost:3001）にアクセス
2. 右上の地球アイコン🌐をクリック
3. 「日本語」または「English」を選択
4. 選択した言語はLocalStorageに保存され、次回訪問時も適用

### Telnet連続コマンド
```bash
# Telnet接続
telnet localhost 23

# ログイン後
Main: N@           # ニュースを自動読み込み
Main: R0@          # 掲示板0番を自動読み込み
Main: R0           # 掲示板0番に移動
Main: E0           # 掲示板0番に直接投稿
```

### データベース初期化
1. 管理UI → Settings → Database セクション
2. "Initialize Database (Reset All Data)" ボタンをクリック
3. 確認ダイアログで "Yes, Initialize Database" をクリック
4. 完了通知を確認

### ユーザー管理
1. 管理UI → Users → ユーザー編集
2. "Active" チェックボックスでアカウント有効/無効切り替え
3. "Require password change on next login" でパスワード変更を強制
