# MTBBS Linux - クイックスタートガイド

## 🚀 最速セットアップ（Docker使用）

### 1. 環境ファイルをコピー
```bash
cd mtbbs-linux
cp .env.example .env
```

### 2. サービスを起動
```bash
docker-compose up -d
```

### 3. テストデータを投入
```bash
docker-compose exec backend python scripts/init_test_data.py
```

### 4. アクセス
- **管理UI**: http://localhost:3000
- **API ドキュメント**: http://localhost:8000/docs
- **Telnet BBS**: `telnet localhost 23`

### 5. ログイン情報
```
管理者:
  User ID: admin
  Password: admin123

テストユーザー:
  User ID: testuser
  Password: test123

ゲスト:
  User ID: guest
  Password: (任意)
```

## 📡 Telnet BBSに接続する

### Windows
```cmd
telnet localhost 23
```

※ Telnetクライアントが無効な場合：
```powershell
# PowerShellで有効化
dism /online /Enable-Feature /FeatureName:TelnetClient
```

### Linux/macOS
```bash
telnet localhost 23
```

### PuTTY（推奨）
1. PuTTYをダウンロード
2. Host: `localhost`, Port: `23`
3. Connection type: `Telnet`

## 🎮 BBSコマンド一覧

### メインメニュー
```
[N]ews     - 新着記事を読む
[R]ead     - メッセージボードを読む
[E]nter    - メッセージを書き込む
[M]ail     - メールを読む
[U]sers    - ユーザーリスト
[W]ho      - ログイン中のユーザー
[H]elp     - ヘルプ
[Q]uit     - ログアウト
```

### 掲示板の使い方
1. メインメニューで `R` を入力
2. ボード番号（例: `1`）を入力
3. 記事リストから読みたい記事番号を入力

### 記事を投稿
1. メインメニューで `E` を入力
2. ボード番号を入力
3. タイトルを入力
4. 本文を入力（`.` だけの行で終了）

## 🖥️ Web管理UIの使い方

### ダッシュボード
- システム統計の確認
- アクティブ接続の監視
- リアルタイム更新

### ユーザー管理
- ユーザーの追加/削除
- アクセス権限の設定
- ログイン履歴の確認

### 掲示板管理
- ボードの作成/編集
- アクセスレベルの設定
- メッセージの管理

## 🛠️ トラブルシューティング

### Telnet接続できない
```bash
# ポート23が使用中の場合
# .envファイルでポートを変更
TELNET_PORT=2323

# 再起動
docker-compose restart backend
```

### データベース接続エラー
```bash
# コンテナの状態を確認
docker-compose ps

# ログを確認
docker-compose logs postgres

# 再起動
docker-compose restart postgres
```

### フロントエンドが表示されない
```bash
# ログ確認
docker-compose logs frontend

# 再ビルド
docker-compose up -d --build frontend
```

## 📊 便利なコマンド

### ログをリアルタイムで表示
```bash
docker-compose logs -f
```

### 特定のサービスのログ
```bash
docker-compose logs -f backend
docker-compose logs -f frontend
docker-compose logs -f postgres
```

### データベースに直接接続
```bash
docker-compose exec postgres psql -U mtbbs -d mtbbs
```

### すべてのコンテナを停止
```bash
docker-compose down
```

### データを含めて完全削除
```bash
docker-compose down -v
```

## 🔧 開発モード

### バックエンド開発
```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

### フロントエンド開発
```bash
cd frontend
npm install
npm run dev
```

## 📝 初期設定のカスタマイズ

### .env ファイルの編集
```env
# データベースパスワードを変更
DB_PASSWORD=your_secure_password

# セキュリティキーを変更
SECRET_KEY=your_secret_key_here

# Telnetポートを変更（Linuxで23番ポートに権限が必要な場合）
TELNET_PORT=2323

# 最大接続数を変更
TELNET_MAX_CONNECTIONS=50
```

### 変更を反映
```bash
docker-compose down
docker-compose up -d
```

## 🎯 次のステップ

1. **掲示板を追加**: 管理UIから新しい掲示板を作成
2. **ユーザーを追加**: ユーザー管理画面から新規ユーザーを登録
3. **メッセージを投稿**: Telnetで接続して記事を投稿
4. **設定をカスタマイズ**: 設定画面でシステムをカスタマイズ

## 📚 詳細ドキュメント

- 完全なドキュメント: [README.md](README.md)
- API仕様: http://localhost:8000/docs
- プロジェクト構造: [README.md#project-structure](README.md#project-structure)

---

**問題が発生した場合**: GitHubのIssuesで報告してください
