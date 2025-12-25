# MTBBS システム監視

## 概要

MTBBS システムの健全性を監視し、問題を早期に検出するための監視システムです。

## 機能

- **ヘルスチェック**: データベース、セッション、ディスク容量、メモリの状態監視
- **メトリクス収集**: システムの稼働状況を定期的に記録
- **セッション追跡**: アクティブなユーザーセッションの管理
- **自動アラート**: 異常検出時のログ記録
- **外部監視対応**: スタンドアロンヘルスチェックスクリプトによる外部監視ツール連携

## システム構成

### 監視コンポーネント

1. **SystemMonitor** (`backend/app/utils/monitor.py`)
   - コアモニタリングエンジン
   - ヘルスチェック機能
   - メトリクス収集機能
   - セッション管理機能

2. **Background Tasks** (Telnet Server統合)
   - 定期ヘルスチェックタスク（5分間隔）
   - 定期メトリクス収集タスク（10分間隔）

3. **Health Check Script** (`scripts/health_check.py`)
   - 外部監視ツール用スタンドアロンスクリプト
   - 終了コードでステータスを報告
   - JSON出力対応

### 監視項目

#### 1. データベースヘルスチェック
- **ファイル存在確認**: データベースファイルの存在
- **整合性チェック**: SQLite PRAGMA quick_check
- **サイズ監視**: データベースファイルサイズ
- **テーブル数確認**: スキーマの健全性

**正常基準**:
- ファイルが存在する
- 整合性チェックが "ok"
- アクセス可能

#### 2. セッション監視
- **アクティブセッション数**: 現在接続中のクライアント数
- **セッション詳細**: client_id, user_id, 接続時刻, 状態
- **ログイン状態追跡**: ゲストユーザーと認証済みユーザーの区別

**正常基準**:
- セッション情報が取得可能
- 異常なセッション数でない（設定上限以内）

#### 3. ディスク容量監視
- **総容量**: ディスクの総容量（GB）
- **使用量**: 現在の使用量（GB、パーセント）
- **空き容量**: 利用可能な空き容量（GB）

**警告閾値**:
- 使用率 90% 以上で警告
- 空き容量不足でバックアップやログ記録に影響

#### 4. メモリ監視（要psutil）
- **プロセスメモリ**: MTBBS プロセスのメモリ使用量（MB）
  - RSS (Resident Set Size): 物理メモリ使用量
  - VMS (Virtual Memory Size): 仮想メモリ使用量
- **システムメモリ**: システム全体のメモリ使用率（%）

**警告閾値**:
- プロセスRSS 500MB 以上で警告
- システムメモリ使用率 90% 以上で警告

**注意**: psutilライブラリが未インストールの場合、メモリ監視は無効化されます。

## 使用方法

### 1. バックグラウンド監視（自動起動）

MTBBS サーバー起動時に自動的に開始されます。

```bash
# サーバー起動（監視も自動的に開始）
./start.sh
```

**バックグラウンドタスク**:
- ヘルスチェック: 5分ごとに実行
- メトリクス収集: 10分ごとに実行

**ログ出力**:
```
[INFO] System monitor initialized: db=data/mtbbs.db, data_dir=data
[INFO] Monitoring background tasks started
[INFO] Health check passed: all components healthy
```

**異常検出時のログ**:
```
[WARNING] Unhealthy components detected: ['disk_space']
[WARNING] Full health report: {'disk_space': {'healthy': False, 'percent_used': 92.5, ...}}
```

### 2. 手動ヘルスチェック

#### 基本的な使用法
```bash
# 標準出力でヘルスチェック実行
python scripts/health_check.py

# 詳細モード
python scripts/health_check.py --verbose

# JSON出力（監視ツール連携用）
python scripts/health_check.py --json

# 問題がある場合のみ出力
python scripts/health_check.py --quiet
```

#### データベースパスのカスタマイズ
```bash
python scripts/health_check.py --db custom/path/mtbbs.db --data-dir custom/data
```

#### 出力例（標準モード）
```
============================================================
MTBBS Health Check Report
============================================================
Timestamp: 2025-01-15T10:30:45.123456

Database: ✅ OK

Sessions: ✅ OK
  - Active: 3

Disk Space: ✅ OK

Memory: ✅ OK

============================================================
✅ System Status: HEALTHY
```

#### 出力例（詳細モード）
```
============================================================
MTBBS Health Check Report
============================================================
Timestamp: 2025-01-15T10:30:45.123456

Database: ✅ OK
  - Integrity: ok
  - Size: 5.23 MB
  - Tables: 8

Sessions: ✅ OK
  - Active: 3
    - 192.168.1.100:54321: user=test_user, state=logged_in
    - 192.168.1.101:54322: user=guest, state=logged_in
    - 192.168.1.102:54323: user=admin, state=logged_in

Disk Space: ✅ OK
  - Total: 500.0 GB
  - Used: 250.5 GB (50.1%)
  - Free: 249.5 GB

Memory: ✅ OK
  - Process RSS: 45.2 MB
  - System Usage: 65.3%

============================================================
✅ System Status: HEALTHY
```

#### 出力例（JSON）
```json
{
  "health": {
    "database": {
      "healthy": true,
      "integrity": "ok",
      "size_bytes": 5483520,
      "size_mb": 5.23,
      "table_count": 8,
      "path": "data/mtbbs.db"
    },
    "sessions": {
      "healthy": true,
      "active_sessions": 3,
      "sessions": [...]
    },
    "disk_space": {
      "healthy": true,
      "total_gb": 500.0,
      "used_gb": 250.5,
      "free_gb": 249.5,
      "percent_used": 50.1,
      "warning_threshold": 90
    },
    "memory": {
      "healthy": true,
      "process_rss_mb": 45.2,
      "process_vms_mb": 123.4,
      "system_percent": 65.3,
      "warning_threshold_process_mb": 500,
      "warning_threshold_system_percent": 90
    },
    "timestamp": "2025-01-15T10:30:45.123456"
  },
  "exit_code": 0,
  "status": "OK"
}
```

### 3. 終了コード

ヘルスチェックスクリプトは以下の終了コードを返します：

- **0**: すべて正常（HEALTHY）
- **1**: 警告レベルの問題あり（WARNING）
  - ディスク容量が90%以上
  - メモリ使用量が閾値以上
- **2**: 重大な問題あり（CRITICAL）
  - データベース異常
  - データベースファイル不存在
- **3**: スクリプト実行エラー

**監視スクリプトでの使用例**:
```bash
#!/bin/bash
python scripts/health_check.py --quiet
EXIT_CODE=$?

if [ $EXIT_CODE -eq 2 ]; then
    echo "CRITICAL: MTBBS health check failed!"
    # アラート送信処理
elif [ $EXIT_CODE -eq 1 ]; then
    echo "WARNING: MTBBS has warnings"
    # 通知送信処理
fi
```

## 外部監視ツール連携

### Cronジョブでの定期チェック

```bash
# crontabを編集
crontab -e

# 10分ごとにヘルスチェック（問題がある場合のみ出力）
*/10 * * * * cd /path/to/mtbbs-linux && python scripts/health_check.py --quiet >> /var/log/mtbbs_health.log 2>&1
```

### Nagios連携例

```bash
# Nagios plugin wrapper
#!/bin/bash
MTBBS_DIR="/path/to/mtbbs-linux"
cd "$MTBBS_DIR"

OUTPUT=$(python scripts/health_check.py --json 2>&1)
EXIT_CODE=$?

case $EXIT_CODE in
    0)
        echo "OK - MTBBS is healthy"
        exit 0
        ;;
    1)
        echo "WARNING - MTBBS has warnings | $OUTPUT"
        exit 1
        ;;
    2)
        echo "CRITICAL - MTBBS is unhealthy | $OUTPUT"
        exit 2
        ;;
    *)
        echo "UNKNOWN - Health check failed | $OUTPUT"
        exit 3
        ;;
esac
```

### Zabbix連携例

```bash
# Zabbix UserParameter
UserParameter=mtbbs.health.status,cd /path/to/mtbbs-linux && python scripts/health_check.py --json 2>/dev/null | jq -r '.status'
UserParameter=mtbbs.health.database,cd /path/to/mtbbs-linux && python scripts/health_check.py --json 2>/dev/null | jq -r '.health.database.healthy'
UserParameter=mtbbs.health.disk_percent,cd /path/to/mtbbs-linux && python scripts/health_check.py --json 2>/dev/null | jq -r '.health.disk_space.percent_used'
UserParameter=mtbbs.health.memory_mb,cd /path/to/mtbbs-linux && python scripts/health_check.py --json 2>/dev/null | jq -r '.health.memory.process_rss_mb'
UserParameter=mtbbs.health.sessions,cd /path/to/mtbbs-linux && python scripts/health_check.py --json 2>/dev/null | jq -r '.health.sessions.active_sessions'
```

### Prometheus Exporter（将来拡張）

メトリクスをPrometheus形式で出力するエクスポーターの実装も可能：

```python
# 例: metrics.py
from prometheus_client import start_http_server, Gauge
from app.utils.monitor import get_monitor
import asyncio

sessions_gauge = Gauge('mtbbs_sessions_active', 'Number of active sessions')
disk_usage_gauge = Gauge('mtbbs_disk_usage_percent', 'Disk usage percentage')

async def collect_metrics():
    monitor = get_monitor()
    health = await monitor.check_health()

    sessions_gauge.set(health['sessions']['active_sessions'])
    disk_usage_gauge.set(health['disk_space']['percent_used'])

if __name__ == '__main__':
    start_http_server(9100)
    # 定期的にメトリクス収集
```

## トラブルシューティング

### ヘルスチェックがエラーになる

**症状**: `RuntimeError: System monitor not initialized`

**原因**: モニターが初期化されていない

**対処**:
```bash
# サーバーが起動していることを確認
ps aux | grep python | grep telnet_server

# サーバーを再起動
./stop.sh && ./start.sh
```

### psutil not found エラー

**症状**: メモリ監視で "psutil not installed" エラー

**原因**: psutilライブラリが未インストール

**対処**:
```bash
# psutilをインストール
pip install psutil

# または requirements.txt に追加済みの場合
pip install -r backend/requirements.txt
```

### ディスク容量警告が頻発する

**症状**: 定期的にディスク容量警告が出る

**原因**: ディスク使用率が90%を超えている

**対処**:
```bash
# 古いバックアップを削除
cd backups
ls -lt *.db
rm mtbbs_YYYYMMDD_HHMMSS.db  # 古いものを手動削除

# またはバックアップ保持期間を短縮
# scripts/backup_database.sh の RETENTION_DAYS を変更

# ログファイルのローテーション確認
sudo logrotate -f /etc/logrotate.d/mtbbs_backup
```

### データベース整合性チェック失敗

**症状**: `Database integrity check failed`

**原因**: データベースファイルが破損している可能性

**対処**:
```bash
# サーバーを停止
./stop.sh

# データベースの整合性を確認
sqlite3 data/mtbbs.db "PRAGMA integrity_check;"

# 問題がある場合、最新のバックアップから復元
cp backups/mtbbs_YYYYMMDD_HHMMSS.db data/mtbbs.db

# 再度整合性チェック
sqlite3 data/mtbbs.db "PRAGMA integrity_check;"

# サーバーを起動
./start.sh
```

### セッション数が異常に多い

**症状**: active_sessions が 100 以上など異常に多い

**原因**:
- 正常に切断されていないセッション
- DDoS攻撃の可能性

**対処**:
```bash
# 現在のセッションを確認
python scripts/health_check.py --verbose

# サーバーを再起動（全セッションクリア）
./stop.sh && ./start.sh

# ファイアウォール設定を確認
sudo iptables -L -n -v

# 接続制限を強化（必要に応じて）
# backend/app/core/config.py の TELNET_MAX_CONNECTIONS を調整
```

## 監視のベストプラクティス

### 1. 定期的なヘルスチェック

```bash
# Cronジョブで10分ごとにヘルスチェック
*/10 * * * * cd /path/to/mtbbs-linux && python scripts/health_check.py --quiet >> /var/log/mtbbs_health.log 2>&1
```

### 2. アラート設定

ディスク容量やデータベース異常時に管理者へ通知：

```bash
#!/bin/bash
# /path/to/mtbbs_alert.sh

cd /path/to/mtbbs-linux
OUTPUT=$(python scripts/health_check.py --json 2>&1)
EXIT_CODE=$?

if [ $EXIT_CODE -ge 1 ]; then
    # メール送信
    echo "$OUTPUT" | mail -s "MTBBS Health Alert" admin@example.com

    # Slackへ通知
    curl -X POST -H 'Content-type: application/json' \
        --data "{\"text\":\"MTBBS Health Alert: $OUTPUT\"}" \
        YOUR_SLACK_WEBHOOK_URL
fi
```

### 3. ログローテーション

```bash
# /etc/logrotate.d/mtbbs_health
/var/log/mtbbs_health.log {
    daily
    rotate 30
    compress
    delaycompress
    missingok
    notifempty
    create 0644 root root
}
```

### 4. メトリクスの可視化

定期的にメトリクスを収集してグラフ化：

```bash
# 簡易的なメトリクス収集スクリプト
#!/bin/bash
# /path/to/collect_metrics.sh

METRICS_FILE="/var/log/mtbbs_metrics.csv"
TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')

cd /path/to/mtbbs-linux
HEALTH=$(python scripts/health_check.py --json 2>/dev/null)

SESSIONS=$(echo "$HEALTH" | jq -r '.health.sessions.active_sessions')
DISK_PERCENT=$(echo "$HEALTH" | jq -r '.health.disk_space.percent_used')
MEMORY_MB=$(echo "$HEALTH" | jq -r '.health.memory.process_rss_mb // 0')

echo "$TIMESTAMP,$SESSIONS,$DISK_PERCENT,$MEMORY_MB" >> "$METRICS_FILE"
```

Cronジョブ:
```bash
# 5分ごとにメトリクス収集
*/5 * * * * /path/to/collect_metrics.sh
```

### 5. 定期的な確認事項

- **日次**: ヘルスチェックログの確認
- **週次**: ディスク容量トレンドの確認
- **月次**: バックアップからの復元テスト
- **四半期**: 監視閾値の見直し

## 設定のカスタマイズ

### 警告閾値の変更

`backend/app/utils/monitor.py` で閾値を調整可能：

```python
# ディスク容量警告閾値（デフォルト: 90%）
healthy = percent_used < 90

# メモリ警告閾値（デフォルト: プロセス500MB、システム90%）
healthy = rss_mb < 500 and system_percent < 90
```

### 監視間隔の変更

`backend/app/protocols/telnet_server.py` で間隔を調整：

```python
# ヘルスチェック間隔（デフォルト: 300秒 = 5分）
periodic_health_check_task(interval=300)

# メトリクス収集間隔（デフォルト: 600秒 = 10分）
periodic_metrics_collection_task(interval=600)
```

## まとめ

MTBBS 監視システムは、システムの健全性を継続的に監視し、問題を早期に検出するための包括的なソリューションです。

**主な利点**:
- 自動的なバックグラウンド監視
- 外部監視ツールとの連携
- JSON出力による柔軟な統合
- 詳細なヘルスレポート
- セッション追跡とメトリクス収集

問題が発生した場合は、ログファイルを確認してください：
```bash
tail -n 100 /var/log/mtbbs_health.log
```

それでも解決しない場合は、GitHub Issuesで報告してください。
