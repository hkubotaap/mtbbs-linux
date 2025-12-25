#!/bin/bash
################################################################################
# MTBBS Database Backup Script
#
# 機能:
# - データベースの自動バックアップ
# - 古いバックアップの自動削除
# - バックアップ検証
# - エラー時のメール通知（オプション）
#
# 使用方法:
#   ./backup_database.sh
#
# Cronジョブ登録例:
#   0 2 * * * /path/to/backup_database.sh >> /var/log/mtbbs_backup.log 2>&1
################################################################################

# 設定
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
BACKUP_DIR="${PROJECT_ROOT}/backups"
DB_PATH="${PROJECT_ROOT}/data/mtbbs.db"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="${BACKUP_DIR}/mtbbs_${DATE}.db"
RETENTION_DAYS=7  # バックアップ保持日数
MIN_BACKUP_SIZE=1024  # 最小バックアップサイズ（バイト）

# カラー出力
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# ログ関数
log_info() {
    echo -e "${GREEN}[INFO]${NC} $(date '+%Y-%m-%d %H:%M:%S') - $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $(date '+%Y-%m-%d %H:%M:%S') - $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $(date '+%Y-%m-%d %H:%M:%S') - $1"
}

# バックアップディレクトリの作成
create_backup_dir() {
    if [ ! -d "$BACKUP_DIR" ]; then
        log_info "Creating backup directory: $BACKUP_DIR"
        mkdir -p "$BACKUP_DIR"
        if [ $? -ne 0 ]; then
            log_error "Failed to create backup directory"
            exit 1
        fi
    fi
}

# データベース存在チェック
check_database() {
    if [ ! -f "$DB_PATH" ]; then
        log_error "Database file not found: $DB_PATH"
        exit 1
    fi
    log_info "Database found: $DB_PATH"
}

# バックアップ実行
perform_backup() {
    log_info "Starting database backup..."
    log_info "Source: $DB_PATH"
    log_info "Destination: $BACKUP_FILE"

    # SQLiteの.backupコマンドを使用
    sqlite3 "$DB_PATH" ".backup '${BACKUP_FILE}'"

    if [ $? -eq 0 ]; then
        log_info "Backup completed successfully"
    else
        log_error "Backup failed"
        exit 1
    fi
}

# バックアップ検証
verify_backup() {
    log_info "Verifying backup integrity..."

    # ファイルサイズチェック
    BACKUP_SIZE=$(stat -f%z "$BACKUP_FILE" 2>/dev/null || stat -c%s "$BACKUP_FILE" 2>/dev/null)

    if [ -z "$BACKUP_SIZE" ]; then
        log_error "Could not determine backup file size"
        return 1
    fi

    if [ "$BACKUP_SIZE" -lt "$MIN_BACKUP_SIZE" ]; then
        log_error "Backup file is too small (${BACKUP_SIZE} bytes). Possible corruption."
        return 1
    fi

    log_info "Backup size: ${BACKUP_SIZE} bytes"

    # SQLiteの整合性チェック
    INTEGRITY_CHECK=$(sqlite3 "$BACKUP_FILE" "PRAGMA integrity_check;" 2>&1)

    if [ "$INTEGRITY_CHECK" = "ok" ]; then
        log_info "Backup integrity check: OK"
        return 0
    else
        log_error "Backup integrity check failed: $INTEGRITY_CHECK"
        return 1
    fi
}

# 古いバックアップの削除
cleanup_old_backups() {
    log_info "Cleaning up backups older than $RETENTION_DAYS days..."

    DELETED_COUNT=0

    # $RETENTION_DAYS日以上前のバックアップを削除
    if [ "$(uname)" = "Darwin" ]; then
        # macOS
        find "$BACKUP_DIR" -name "mtbbs_*.db" -type f -mtime +${RETENTION_DAYS} | while read -r old_backup; do
            log_info "Deleting old backup: $(basename "$old_backup")"
            rm -f "$old_backup"
            DELETED_COUNT=$((DELETED_COUNT + 1))
        done
    else
        # Linux
        find "$BACKUP_DIR" -name "mtbbs_*.db" -type f -mtime +${RETENTION_DAYS} -delete
        DELETED_COUNT=$(find "$BACKUP_DIR" -name "mtbbs_*.db" -type f -mtime +${RETENTION_DAYS} | wc -l)
    fi

    if [ "$DELETED_COUNT" -gt 0 ]; then
        log_info "Deleted $DELETED_COUNT old backup(s)"
    else
        log_info "No old backups to delete"
    fi
}

# バックアップ統計表示
show_backup_stats() {
    TOTAL_BACKUPS=$(find "$BACKUP_DIR" -name "mtbbs_*.db" -type f | wc -l)
    TOTAL_SIZE=$(du -sh "$BACKUP_DIR" 2>/dev/null | awk '{print $1}')

    log_info "Backup statistics:"
    log_info "  Total backups: $TOTAL_BACKUPS"
    log_info "  Total size: $TOTAL_SIZE"
}

# エラーハンドラ
handle_error() {
    log_error "Backup process failed. Check logs for details."

    # オプション: メール通知（mailコマンドが利用可能な場合）
    if command -v mail >/dev/null 2>&1; then
        if [ -n "$ADMIN_EMAIL" ]; then
            echo "MTBBS backup failed at $(date). Check server logs." | mail -s "MTBBS Backup Failed" "$ADMIN_EMAIL"
            log_info "Error notification sent to $ADMIN_EMAIL"
        fi
    fi

    exit 1
}

# メイン処理
main() {
    log_info "========================================" log_info "MTBBS Database Backup Started"
    log_info "========================================"

    # エラー時のハンドラを設定
    trap handle_error ERR

    # 1. バックアップディレクトリ作成
    create_backup_dir

    # 2. データベース存在チェック
    check_database

    # 3. バックアップ実行
    perform_backup

    # 4. バックアップ検証
    if ! verify_backup; then
        log_error "Backup verification failed. Removing corrupt backup."
        rm -f "$BACKUP_FILE"
        exit 1
    fi

    # 5. 古いバックアップの削除
    cleanup_old_backups

    # 6. 統計表示
    show_backup_stats

    log_info "========================================"
    log_info "MTBBS Database Backup Completed Successfully"
    log_info "========================================"

    exit 0
}

# スクリプト実行
main "$@"
