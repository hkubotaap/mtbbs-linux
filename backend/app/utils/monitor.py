"""
システム監視ユーティリティ

データベース、セッション、ディスク容量、システムメトリクスの監視を提供します。
"""

import os
import asyncio
import logging
import sqlite3
import shutil
from typing import Dict, Any, Optional
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)


class SystemMonitor:
    """システム監視クラス"""

    def __init__(self, db_path: str, data_dir: str):
        """
        初期化

        Args:
            db_path: データベースファイルパス
            data_dir: データディレクトリパス
        """
        self.db_path = db_path
        self.data_dir = data_dir
        self.active_sessions = {}
        self.metrics_history = []

    async def check_health(self) -> Dict[str, Any]:
        """
        総合ヘルスチェック

        Returns:
            ヘルスチェック結果の辞書
        """
        checks = {
            'database': await self.check_database(),
            'sessions': await self.check_sessions(),
            'disk_space': await self.check_disk_space(),
            'memory': await self.check_memory(),
            'timestamp': datetime.now().isoformat()
        }

        # 異常があればログに記録
        if not all(checks[k]['healthy'] for k in ['database', 'sessions', 'disk_space', 'memory']):
            logger.warning(f"Health check failed: {checks}")

        return checks

    async def check_database(self) -> Dict[str, Any]:
        """
        データベースヘルスチェック

        Returns:
            データベース状態情報
        """
        try:
            # データベースファイルの存在確認
            if not os.path.exists(self.db_path):
                return {
                    'healthy': False,
                    'error': 'Database file not found',
                    'path': self.db_path
                }

            # ファイルサイズ取得
            db_size = os.path.getsize(self.db_path)

            # 整合性チェック（軽量版）
            conn = sqlite3.connect(self.db_path, timeout=5.0)
            cursor = conn.cursor()

            # クイックチェック（PRAGMA quick_check は高速）
            cursor.execute("PRAGMA quick_check")
            integrity = cursor.fetchone()[0]

            # テーブル数取得
            cursor.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table'")
            table_count = cursor.fetchone()[0]

            conn.close()

            return {
                'healthy': integrity == 'ok',
                'integrity': integrity,
                'size_bytes': db_size,
                'size_mb': round(db_size / 1024 / 1024, 2),
                'table_count': table_count,
                'path': self.db_path
            }

        except sqlite3.Error as e:
            logger.error(f"Database health check failed: {e}")
            return {
                'healthy': False,
                'error': str(e)
            }
        except Exception as e:
            logger.error(f"Unexpected error in database health check: {e}")
            return {
                'healthy': False,
                'error': str(e)
            }

    async def check_sessions(self) -> Dict[str, Any]:
        """
        セッションヘルスチェック

        Returns:
            セッション状態情報
        """
        try:
            active_count = len(self.active_sessions)

            # セッション情報収集
            session_info = []
            for client_id, session_data in self.active_sessions.items():
                session_info.append({
                    'client_id': client_id,
                    'user_id': session_data.get('user_id'),
                    'connected_at': session_data.get('connected_at'),
                    'state': session_data.get('state')
                })

            return {
                'healthy': True,
                'active_sessions': active_count,
                'sessions': session_info
            }

        except Exception as e:
            logger.error(f"Session health check failed: {e}")
            return {
                'healthy': False,
                'error': str(e)
            }

    async def check_disk_space(self) -> Dict[str, Any]:
        """
        ディスク容量チェック

        Returns:
            ディスク容量情報
        """
        try:
            # データディレクトリのディスク使用状況
            usage = shutil.disk_usage(self.data_dir)

            total_gb = usage.total / (1024 ** 3)
            used_gb = usage.used / (1024 ** 3)
            free_gb = usage.free / (1024 ** 3)
            percent_used = (usage.used / usage.total) * 100

            # 警告閾値: 90%以上で警告
            healthy = percent_used < 90

            if not healthy:
                logger.warning(f"Low disk space: {percent_used:.1f}% used")

            return {
                'healthy': healthy,
                'total_gb': round(total_gb, 2),
                'used_gb': round(used_gb, 2),
                'free_gb': round(free_gb, 2),
                'percent_used': round(percent_used, 2),
                'warning_threshold': 90
            }

        except Exception as e:
            logger.error(f"Disk space check failed: {e}")
            return {
                'healthy': False,
                'error': str(e)
            }

    async def check_memory(self) -> Dict[str, Any]:
        """
        メモリ使用状況チェック

        Returns:
            メモリ使用情報
        """
        try:
            import psutil

            # プロセスのメモリ使用状況
            process = psutil.Process()
            memory_info = process.memory_info()

            rss_mb = memory_info.rss / (1024 ** 2)  # Resident Set Size
            vms_mb = memory_info.vms / (1024 ** 2)  # Virtual Memory Size

            # システム全体のメモリ
            system_memory = psutil.virtual_memory()
            system_percent = system_memory.percent

            # 警告閾値: プロセスが500MB以上使用、またはシステムが90%以上
            healthy = rss_mb < 500 and system_percent < 90

            if not healthy:
                logger.warning(f"High memory usage: Process={rss_mb:.1f}MB, System={system_percent}%")

            return {
                'healthy': healthy,
                'process_rss_mb': round(rss_mb, 2),
                'process_vms_mb': round(vms_mb, 2),
                'system_percent': round(system_percent, 2),
                'warning_threshold_process_mb': 500,
                'warning_threshold_system_percent': 90
            }

        except ImportError:
            # psutil がインストールされていない場合
            return {
                'healthy': True,
                'error': 'psutil not installed - memory monitoring unavailable'
            }
        except Exception as e:
            logger.error(f"Memory check failed: {e}")
            return {
                'healthy': False,
                'error': str(e)
            }

    def register_session(self, client_id: str, user_id: Optional[str] = None, state: str = "connected"):
        """
        セッション登録

        Args:
            client_id: クライアントID
            user_id: ユーザーID（ログイン後）
            state: セッション状態
        """
        self.active_sessions[client_id] = {
            'user_id': user_id,
            'connected_at': datetime.now().isoformat(),
            'state': state
        }

    def unregister_session(self, client_id: str):
        """
        セッション登録解除

        Args:
            client_id: クライアントID
        """
        if client_id in self.active_sessions:
            del self.active_sessions[client_id]

    def update_session_state(self, client_id: str, user_id: Optional[str] = None, state: Optional[str] = None):
        """
        セッション状態更新

        Args:
            client_id: クライアントID
            user_id: ユーザーID
            state: セッション状態
        """
        if client_id in self.active_sessions:
            if user_id is not None:
                self.active_sessions[client_id]['user_id'] = user_id
            if state is not None:
                self.active_sessions[client_id]['state'] = state

    async def collect_metrics(self) -> Dict[str, Any]:
        """
        システムメトリクス収集

        Returns:
            収集されたメトリクス
        """
        metrics = {
            'timestamp': datetime.now().isoformat(),
            'health': await self.check_health(),
            'uptime': self._get_uptime()
        }

        # 履歴に追加（最大100件保持）
        self.metrics_history.append(metrics)
        if len(self.metrics_history) > 100:
            self.metrics_history.pop(0)

        return metrics

    def _get_uptime(self) -> Dict[str, Any]:
        """
        アップタイム取得（簡易版）

        Returns:
            アップタイム情報
        """
        try:
            import psutil
            boot_time = datetime.fromtimestamp(psutil.boot_time())
            uptime = datetime.now() - boot_time

            return {
                'boot_time': boot_time.isoformat(),
                'uptime_seconds': int(uptime.total_seconds()),
                'uptime_days': uptime.days,
                'uptime_hours': uptime.seconds // 3600
            }
        except ImportError:
            return {
                'error': 'psutil not installed - uptime unavailable'
            }
        except Exception as e:
            return {
                'error': str(e)
            }

    def get_metrics_history(self, limit: int = 10) -> list:
        """
        メトリクス履歴取得

        Args:
            limit: 取得件数

        Returns:
            メトリクス履歴のリスト
        """
        return self.metrics_history[-limit:]


# グローバルモニターインスタンス
_monitor: Optional[SystemMonitor] = None


def initialize_monitor(db_path: str, data_dir: str):
    """
    グローバルモニターの初期化

    Args:
        db_path: データベースファイルパス
        data_dir: データディレクトリパス
    """
    global _monitor
    _monitor = SystemMonitor(db_path, data_dir)
    logger.info(f"System monitor initialized: db={db_path}, data_dir={data_dir}")


def get_monitor() -> SystemMonitor:
    """
    グローバルモニターインスタンスを取得

    Returns:
        SystemMonitor インスタンス

    Raises:
        RuntimeError: モニターが初期化されていない場合
    """
    if _monitor is None:
        raise RuntimeError("System monitor not initialized. Call initialize_monitor() first.")
    return _monitor


# 定期的なヘルスチェックタスク
async def periodic_health_check_task(interval: int = 300):
    """
    定期ヘルスチェックタスク

    Args:
        interval: チェック間隔（秒）
    """
    monitor = get_monitor()

    while True:
        try:
            await asyncio.sleep(interval)
            health = await monitor.check_health()

            # 異常があればログに記録
            unhealthy_components = [
                component for component, status in health.items()
                if isinstance(status, dict) and not status.get('healthy', True)
            ]

            if unhealthy_components:
                logger.warning(f"Unhealthy components detected: {unhealthy_components}")
                logger.warning(f"Full health report: {health}")
            else:
                logger.info(f"Health check passed: all components healthy")

        except Exception as e:
            logger.error(f"Periodic health check failed: {e}")


# 定期的なメトリクス収集タスク
async def periodic_metrics_collection_task(interval: int = 600):
    """
    定期メトリクス収集タスク

    Args:
        interval: 収集間隔（秒）
    """
    monitor = get_monitor()

    while True:
        try:
            await asyncio.sleep(interval)
            metrics = await monitor.collect_metrics()
            logger.info(f"Metrics collected: sessions={metrics['health']['sessions']['active_sessions']}, "
                       f"disk_free={metrics['health']['disk_space']['free_gb']}GB")

        except Exception as e:
            logger.error(f"Periodic metrics collection failed: {e}")
