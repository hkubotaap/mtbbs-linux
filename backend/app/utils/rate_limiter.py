"""
レート制限ユーティリティ

ログイン試行やコマンド実行の頻度制限を提供します。
"""

import time
from functools import wraps
from typing import Dict, Callable, Any
from collections import defaultdict
import asyncio


class RateLimiter:
    """レート制限管理クラス"""

    def __init__(self):
        self.call_history: Dict[str, list] = defaultdict(list)

    def check_rate_limit(
        self,
        key: str,
        max_calls: int,
        period: int
    ) -> tuple[bool, int]:
        """
        レート制限チェック

        Args:
            key: 識別キー（通常はIP or user_id）
            max_calls: 期間内の最大呼び出し回数
            period: 期間（秒）

        Returns:
            (制限内かどうか, 残り回数)
        """
        now = time.time()

        # 期限切れの履歴を削除
        self.call_history[key] = [
            timestamp for timestamp in self.call_history[key]
            if timestamp > now - period
        ]

        current_calls = len(self.call_history[key])

        if current_calls >= max_calls:
            return False, 0

        return True, max_calls - current_calls

    def record_call(self, key: str):
        """呼び出しを記録"""
        self.call_history[key].append(time.time())

    def reset(self, key: str):
        """特定キーの履歴をリセット"""
        if key in self.call_history:
            del self.call_history[key]

    def cleanup_expired(self, max_age: int = 3600):
        """
        古い履歴をクリーンアップ

        Args:
            max_age: 保持する最大期間（秒）
        """
        now = time.time()
        keys_to_delete = []

        for key, timestamps in self.call_history.items():
            # 全ての履歴が古い場合は削除対象
            if all(timestamp < now - max_age for timestamp in timestamps):
                keys_to_delete.append(key)

        for key in keys_to_delete:
            del self.call_history[key]


# グローバルレート制限インスタンス
_rate_limiter = RateLimiter()


def rate_limit(max_calls: int, period: int, key_func: Callable = None):
    """
    レート制限デコレータ

    Args:
        max_calls: 期間内の最大呼び出し回数
        period: 期間（秒）
        key_func: キー生成関数（デフォルトはself.client_idまたはself.user_id）

    使用例:
        @rate_limit(max_calls=3, period=60)
        async def login(self):
            # ログイン処理
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(self, *args, **kwargs) -> Any:
            # キーの決定
            if key_func:
                key = key_func(self)
            else:
                # デフォルト: client_id or user_id を使用
                key = getattr(self, 'client_id', None) or getattr(self, 'user_id', None)
                if not key:
                    # キーがない場合は制限なし
                    return await func(self, *args, **kwargs)

            # レート制限チェック
            allowed, remaining = _rate_limiter.check_rate_limit(key, max_calls, period)

            if not allowed:
                # 制限超過
                if hasattr(self, 'send_line'):
                    await self.send_line(
                        f"Rate limit exceeded. Please wait {period} seconds."
                    )
                raise RateLimitExceeded(
                    f"Rate limit exceeded for {func.__name__}: "
                    f"{max_calls} calls per {period} seconds"
                )

            # 呼び出しを記録
            _rate_limiter.record_call(key)

            # 実際の関数を実行
            return await func(self, *args, **kwargs)

        return wrapper
    return decorator


class RateLimitExceeded(Exception):
    """レート制限超過例外"""
    pass


def get_rate_limiter() -> RateLimiter:
    """グローバルレート制限インスタンスを取得"""
    return _rate_limiter


# 定期的なクリーンアップタスク
async def rate_limiter_cleanup_task(interval: int = 3600):
    """
    レート制限履歴の定期クリーンアップタスク

    Args:
        interval: クリーンアップ間隔（秒）
    """
    while True:
        await asyncio.sleep(interval)
        _rate_limiter.cleanup_expired(max_age=interval * 2)
