# MTBBS バックアップシステム

## 概要

MTBBS データベースの自動バックアップシステムです。

## 機能

- **自動バックアップ**: SQLiteデータベースの完全バックアップ
- **整合性チェック**: バックアップファイルの検証
- **自動クリーンアップ**: 古いバックアップの自動削除（デフォルト7日）
- **ログ記録**: バックアップ処理の詳細ログ
- **エラー通知**: 失敗時のメール通知（オプション）

## インストール

### 1. スクリプトの配置

スクリプトは既に`scripts/backup_database.sh`に配置されています。

### 2. バックアップディレクトリの作成

```bash
mkdir -p backups
```

### 3. 権限の確認

```bash
chmod +x scripts/backup_database.sh
```

## 使用方法

### 手動バックアップ

```bash
./scripts/backup_database.sh
```

### Cronジョブでの自動化

#### 毎日午前2時に実行する場合:

```bash
# crontabを編集
crontab -e

# 以下の行を追加
0 2 * * * cd /path/to/mtbbs-linux && ./scripts/backup_database.sh >> /var/log/mtbbs_backup.log 2>&1
```

#### ログローテーション設定（推奨）

`/etc/logrotate.d/mtbbs_backup`を作成:

```
/var/log/mtbbs_backup.log {
    daily
    rotate 14
    compress
    delaycompress
    missingok
    notifempty
    create 0644 root root
}
```

## 設定

`backup_database.sh`内の以下の変数で設定をカスタマイズできます:

```bash
BACKUP_DIR="${PROJECT_ROOT}/backups"     # バックアップ保存先
RETENTION_DAYS=7                          # バックアップ保持日数
MIN_BACKUP_SIZE=1024                      # 最小バックアップサイズ（バイト）
```

### エラー通知の有効化

メール通知を有効にするには、cronジョブに環境変数を設定:

```bash
ADMIN_EMAIL=admin@example.com
0 2 * * * cd /path/to/mtbbs-linux && ADMIN_EMAIL=$ADMIN_EMAIL ./scripts/backup_database.sh >> /var/log/mtbbs_backup.log 2>&1
```

## バックアップからの復元

### 1. バックアップファイルの確認

```bash
ls -lh backups/
```

### 2. システムの停止

```bash
./stop.sh
```

### 3. 現在のデータベースのバックアップ（念のため）

```bash
cp data/mtbbs.db data/mtbbs.db.before_restore
```

### 4. バックアップからの復元

```bash
cp backups/mtbbs_YYYYMMDD_HHMMSS.db data/mtbbs.db
```

### 5. 整合性チェック

```bash
sqlite3 data/mtbbs.db "PRAGMA integrity_check;"
```

結果が`ok`であることを確認してください。

### 6. システムの再起動

```bash
./start.sh
```

## トラブルシューティング

### バックアップが失敗する

**症状**: バックアップスクリプトがエラーを返す

**原因と対処**:

1. **データベースファイルが存在しない**
   ```bash
   ls -l data/mtbbs.db
   ```
   ファイルが存在しない場合は、アプリケーションを起動してデータベースを初期化してください。

2. **権限不足**
   ```bash
   chmod 644 data/mtbbs.db
   chmod 755 backups/
   ```

3. **ディスク容量不足**
   ```bash
   df -h
   ```
   バックアップディレクトリのあるパーティションの空き容量を確認してください。

### バックアップファイルが破損している

**症状**: 整合性チェックが失敗する

**対処**:

1. 前回のバックアップを確認:
   ```bash
   ls -lt backups/ | head -5
   ```

2. 別のバックアップファイルで復元を試みる

3. 最終手段として、現在のデータベースから復旧:
   ```bash
   sqlite3 data/mtbbs.db ".recover" | sqlite3 recovered.db
   ```

## ベストプラクティス

### 1. オフサイトバックアップ

ローカルバックアップに加えて、リモートストレージへのコピーを推奨:

```bash
# rsyncを使った例
rsync -avz backups/ user@remote-server:/backup/mtbbs/
```

### 2. バックアップテスト

月に1回、バックアップからの復元をテスト環境で実施することを推奨します。

### 3. 監視設定

Cronジョブが正常に動作しているか定期的に確認:

```bash
grep "Backup Completed Successfully" /var/log/mtbbs_backup.log | tail -5
```

### 4. バックアップ前のメンテナンス

定期的にデータベースの最適化を実施:

```bash
sqlite3 data/mtbbs.db "VACUUM;"
sqlite3 data/mtbbs.db "ANALYZE;"
```

## バックアップスケジュール例

| 頻度 | タイミング | 保持期間 | 用途 |
|-----|----------|---------|------|
| 毎日 | 午前2時 | 7日間 | 日次バックアップ |
| 毎週 | 日曜日午前3時 | 4週間 | 週次バックアップ |
| 毎月 | 1日午前4時 | 12ヶ月 | 月次バックアップ |

### Cron設定例（複数バックアップ）

```bash
# 日次バックアップ（7日保持）
0 2 * * * cd /path/to/mtbbs-linux && ./scripts/backup_database.sh

# 週次バックアップ（4週保持）
0 3 * * 0 cp data/mtbbs.db backups/weekly/mtbbs_$(date +\%Y\%m\%d).db && find backups/weekly -name "*.db" -mtime +28 -delete

# 月次バックアップ（12ヶ月保持）
0 4 1 * * cp data/mtbbs.db backups/monthly/mtbbs_$(date +\%Y\%m).db && find backups/monthly -name "*.db" -mtime +365 -delete
```

## サポート

問題が発生した場合は、ログファイルを確認してください:

```bash
tail -n 50 /var/log/mtbbs_backup.log
```

それでも解決しない場合は、GitHub Issuesで報告してください。
