"""
入力サニタイゼーションユーティリティ

ユーザー入力から危険な文字列やパターンを除去・エスケープします。
"""

import re
from typing import Optional


class InputSanitizer:
    """入力サニタイゼーションクラス"""

    # 危険なSQLパターン
    SQL_INJECTION_PATTERNS = [
        r"(\b(SELECT|INSERT|UPDATE|DELETE|DROP|CREATE|ALTER|EXEC|EXECUTE)\b)",
        r"(--|\#|\/\*|\*\/)",
        r"(\bOR\b.*\b=\b)",
        r"(\bAND\b.*\b=\b)",
        r"(;.*\b(SELECT|INSERT|UPDATE|DELETE)\b)",
    ]

    # XSSパターン
    XSS_PATTERNS = [
        r"<script[^>]*>.*?</script>",
        r"javascript:",
        r"on\w+\s*=",  # onload=, onclick=, etc.
    ]

    # 制御文字パターン（改行・タブ以外）
    CONTROL_CHARS = r"[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]"

    @staticmethod
    def sanitize_text(
        text: str,
        max_length: Optional[int] = None,
        allow_newlines: bool = True
    ) -> str:
        """
        テキスト入力をサニタイズ

        Args:
            text: サニタイズ対象のテキスト
            max_length: 最大長（Noneの場合は無制限）
            allow_newlines: 改行を許可するか

        Returns:
            サニタイズされたテキスト
        """
        if not text:
            return ""

        # 制御文字の除去
        if allow_newlines:
            # 改行とタブは保持
            sanitized = re.sub(InputSanitizer.CONTROL_CHARS, "", text)
        else:
            # すべての制御文字を除去
            sanitized = re.sub(r"[\x00-\x1F\x7F]", "", text)

        # 最大長の制限
        if max_length and len(sanitized) > max_length:
            sanitized = sanitized[:max_length]

        return sanitized.strip()

    @staticmethod
    def sanitize_user_id(user_id: str) -> str:
        """
        ユーザーIDをサニタイズ

        Args:
            user_id: ユーザーID

        Returns:
            サニタイズされたユーザーID（英数字とアンダースコアのみ）
        """
        if not user_id:
            return ""

        # 英数字とアンダースコア、ハイフンのみ許可
        sanitized = re.sub(r"[^a-zA-Z0-9_-]", "", user_id)

        # 最大8文字
        return sanitized[:8].strip()

    @staticmethod
    def sanitize_title(title: str) -> str:
        """
        タイトルをサニタイズ

        Args:
            title: タイトル

        Returns:
            サニタイズされたタイトル
        """
        # XSSパターンの除去
        sanitized = title
        for pattern in InputSanitizer.XSS_PATTERNS:
            sanitized = re.sub(pattern, "", sanitized, flags=re.IGNORECASE)

        # 基本サニタイゼーション
        sanitized = InputSanitizer.sanitize_text(
            sanitized,
            max_length=100,
            allow_newlines=False
        )

        return sanitized

    @staticmethod
    def sanitize_message_body(body: str) -> str:
        """
        メッセージ本文をサニタイズ

        Args:
            body: メッセージ本文

        Returns:
            サニタイズされた本文
        """
        # XSSパターンの除去
        sanitized = body
        for pattern in InputSanitizer.XSS_PATTERNS:
            sanitized = re.sub(pattern, "", sanitized, flags=re.IGNORECASE)

        # 基本サニタイゼーション（改行は許可）
        sanitized = InputSanitizer.sanitize_text(
            sanitized,
            max_length=10000,
            allow_newlines=True
        )

        return sanitized

    @staticmethod
    def detect_sql_injection(text: str) -> bool:
        """
        SQLインジェクションの可能性を検出

        Args:
            text: チェック対象のテキスト

        Returns:
            SQLインジェクションパターンが検出された場合True
        """
        for pattern in InputSanitizer.SQL_INJECTION_PATTERNS:
            if re.search(pattern, text, re.IGNORECASE):
                return True
        return False

    @staticmethod
    def detect_xss(text: str) -> bool:
        """
        XSSの可能性を検出

        Args:
            text: チェック対象のテキスト

        Returns:
            XSSパターンが検出された場合True
        """
        for pattern in InputSanitizer.XSS_PATTERNS:
            if re.search(pattern, text, re.IGNORECASE):
                return True
        return False

    @staticmethod
    def validate_email(email: str) -> bool:
        """
        メールアドレスの簡易バリデーション

        Args:
            email: メールアドレス

        Returns:
            有効な形式の場合True
        """
        if not email:
            return False

        # 簡易的なメールアドレスパターン
        pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
        return bool(re.match(pattern, email))

    @staticmethod
    def sanitize_command(command: str) -> str:
        """
        コマンド入力をサニタイズ

        Args:
            command: コマンド文字列

        Returns:
            サニタイズされたコマンド（英数字と一部記号のみ）
        """
        if not command:
            return ""

        # コマンドで許可される文字: 英数字、@、#、_、-、/、?、*
        sanitized = re.sub(r"[^a-zA-Z0-9@#_\-/?*]", "", command)

        # 最大255文字
        return sanitized[:255].strip()


# グローバルインスタンス
_sanitizer = InputSanitizer()


def sanitize_text(text: str, max_length: Optional[int] = None, allow_newlines: bool = True) -> str:
    """テキストサニタイゼーション（便利関数）"""
    return _sanitizer.sanitize_text(text, max_length, allow_newlines)


def sanitize_user_id(user_id: str) -> str:
    """ユーザーIDサニタイゼーション（便利関数）"""
    return _sanitizer.sanitize_user_id(user_id)


def sanitize_title(title: str) -> str:
    """タイトルサニタイゼーション（便利関数）"""
    return _sanitizer.sanitize_title(title)


def sanitize_message_body(body: str) -> str:
    """メッセージ本文サニタイゼーション（便利関数）"""
    return _sanitizer.sanitize_message_body(body)


def sanitize_command(command: str) -> str:
    """コマンドサニタイゼーション（便利関数）"""
    return _sanitizer.sanitize_command(command)


def detect_sql_injection(text: str) -> bool:
    """SQLインジェクション検出（便利関数）"""
    return _sanitizer.detect_sql_injection(text)


def detect_xss(text: str) -> bool:
    """XSS検出（便利関数）"""
    return _sanitizer.detect_xss(text)


def validate_email(email: str) -> bool:
    """メールアドレス検証（便利関数）"""
    return _sanitizer.validate_email(email)
