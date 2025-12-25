#!/usr/bin/env python3
"""
MTBBS Health Check Script

外部監視ツールやCronジョブから実行可能なヘルスチェックスクリプト。
終了コードでステータスを返します。

終了コード:
  0: すべて正常
  1: 警告レベルの問題あり
  2: 重大な問題あり
  3: スクリプト実行エラー
"""

import sys
import os
import asyncio
import json
from pathlib import Path

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from backend.app.utils.monitor import SystemMonitor


def print_health_report(health: dict, verbose: bool = False):
    """
    ヘルスチェック結果を出力

    Args:
        health: ヘルスチェック結果
        verbose: 詳細出力モード
    """
    print("=" * 60)
    print("MTBBS Health Check Report")
    print("=" * 60)
    print(f"Timestamp: {health.get('timestamp', 'N/A')}")
    print()

    # データベース
    db = health.get('database', {})
    db_status = "✅ OK" if db.get('healthy') else "❌ FAILED"
    print(f"Database: {db_status}")
    if verbose or not db.get('healthy'):
        print(f"  - Integrity: {db.get('integrity', 'N/A')}")
        print(f"  - Size: {db.get('size_mb', 'N/A')} MB")
        print(f"  - Tables: {db.get('table_count', 'N/A')}")
        if 'error' in db:
            print(f"  - Error: {db['error']}")
    print()

    # セッション
    sessions = health.get('sessions', {})
    sessions_status = "✅ OK" if sessions.get('healthy') else "❌ FAILED"
    print(f"Sessions: {sessions_status}")
    print(f"  - Active: {sessions.get('active_sessions', 0)}")
    if verbose and sessions.get('sessions'):
        for session in sessions['sessions']:
            print(f"    - {session['client_id']}: user={session.get('user_id', 'guest')}, "
                  f"state={session.get('state', 'unknown')}")
    if 'error' in sessions:
        print(f"  - Error: {sessions['error']}")
    print()

    # ディスク容量
    disk = health.get('disk_space', {})
    disk_status = "✅ OK" if disk.get('healthy') else "⚠️ WARNING"
    print(f"Disk Space: {disk_status}")
    if verbose or not disk.get('healthy'):
        print(f"  - Total: {disk.get('total_gb', 'N/A')} GB")
        print(f"  - Used: {disk.get('used_gb', 'N/A')} GB ({disk.get('percent_used', 'N/A')}%)")
        print(f"  - Free: {disk.get('free_gb', 'N/A')} GB")
        if 'error' in disk:
            print(f"  - Error: {disk['error']}")
    print()

    # メモリ
    memory = health.get('memory', {})
    memory_status = "✅ OK" if memory.get('healthy') else "⚠️ WARNING"
    print(f"Memory: {memory_status}")
    if verbose or not memory.get('healthy'):
        if 'process_rss_mb' in memory:
            print(f"  - Process RSS: {memory.get('process_rss_mb', 'N/A')} MB")
            print(f"  - System Usage: {memory.get('system_percent', 'N/A')}%")
        if 'error' in memory:
            print(f"  - {memory['error']}")
    print()

    print("=" * 60)


def determine_exit_code(health: dict) -> int:
    """
    ヘルスチェック結果から終了コードを決定

    Args:
        health: ヘルスチェック結果

    Returns:
        終了コード (0=正常, 1=警告, 2=重大)
    """
    # 重大な問題のチェック
    critical_components = ['database']
    for component in critical_components:
        if component in health and not health[component].get('healthy'):
            return 2

    # 警告レベルのチェック
    warning_components = ['disk_space', 'memory']
    for component in warning_components:
        if component in health and not health[component].get('healthy'):
            return 1

    return 0


async def main():
    """メイン処理"""
    import argparse

    parser = argparse.ArgumentParser(description='MTBBS Health Check')
    parser.add_argument('--db', default='data/mtbbs.db',
                       help='Database file path (default: data/mtbbs.db)')
    parser.add_argument('--data-dir', default='data',
                       help='Data directory path (default: data)')
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='Verbose output')
    parser.add_argument('--json', action='store_true',
                       help='Output as JSON')
    parser.add_argument('--quiet', '-q', action='store_true',
                       help='Only output on failure')

    args = parser.parse_args()

    # データベースパスを絶対パスに変換
    db_path = os.path.join(project_root, args.db)
    data_dir = os.path.join(project_root, args.data_dir)

    # モニターを初期化
    monitor = SystemMonitor(db_path, data_dir)

    try:
        # ヘルスチェック実行
        health = await monitor.check_health()

        # 終了コード決定
        exit_code = determine_exit_code(health)

        # 出力
        if args.json:
            # JSON出力
            output = {
                'health': health,
                'exit_code': exit_code,
                'status': 'OK' if exit_code == 0 else ('WARNING' if exit_code == 1 else 'CRITICAL')
            }
            print(json.dumps(output, indent=2, ensure_ascii=False))
        elif not args.quiet or exit_code != 0:
            # 通常出力（または失敗時のみ）
            print_health_report(health, verbose=args.verbose)

            if exit_code == 0:
                print("✅ System Status: HEALTHY")
            elif exit_code == 1:
                print("⚠️ System Status: WARNING - Some components need attention")
            else:
                print("❌ System Status: CRITICAL - Immediate action required")

        return exit_code

    except Exception as e:
        print(f"❌ Health check script failed: {e}", file=sys.stderr)
        return 3


if __name__ == '__main__':
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\nHealth check interrupted", file=sys.stderr)
        sys.exit(3)
    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        sys.exit(3)
