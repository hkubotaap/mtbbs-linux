# -*- coding: utf-8 -*-
"""
Message Service - System Message Management
"""
from typing import List, Optional
from sqlalchemy import select
from app.models.system_message import SystemMessage
from app.core.database import async_session
from app.resources.messages_ja import (
    MAIN_MENU, FILE_MENU, READ_MENU, INSTALL_MENU, CHAT_MENU, SYSOP_MENU,
    OPENING_MESSAGE, LOGIN_MESSAGE, LOGOUT_MESSAGE, HELP_MESSAGE,
    SYSINFO_MESSAGE, HOST_VERSION, CHAT_ROOM_OPENING, FILE_BOARD_INFO,
    MTBBS_VERSION
)


class MessageService:
    """Service for managing system messages"""

    async def get_all_messages(self) -> List[SystemMessage]:
        """Get all system messages"""
        async with async_session() as session:
            result = await session.execute(select(SystemMessage))
            return result.scalars().all()

    async def get_messages_by_category(self, category: str) -> List[SystemMessage]:
        """Get messages filtered by category"""
        async with async_session() as session:
            result = await session.execute(
                select(SystemMessage).where(SystemMessage.category == category)
            )
            return result.scalars().all()

    async def get_message_by_key(self, message_key: str) -> Optional[SystemMessage]:
        """Get a specific message by its key"""
        async with async_session() as session:
            result = await session.execute(
                select(SystemMessage).where(SystemMessage.message_key == message_key)
            )
            return result.scalar_one_or_none()

    async def create_message(self, message_data: dict) -> SystemMessage:
        """Create a new system message"""
        async with async_session() as session:
            message = SystemMessage(**message_data)
            session.add(message)
            await session.commit()
            await session.refresh(message)
            return message

    async def update_message(self, message_key: str, message_data: dict) -> Optional[SystemMessage]:
        """Update an existing message"""
        async with async_session() as session:
            result = await session.execute(
                select(SystemMessage).where(SystemMessage.message_key == message_key)
            )
            message = result.scalar_one_or_none()

            if not message:
                return None

            for key, value in message_data.items():
                if hasattr(message, key):
                    setattr(message, key, value)

            await session.commit()
            await session.refresh(message)
            return message

    async def delete_message(self, message_key: str) -> bool:
        """Delete a message"""
        async with async_session() as session:
            result = await session.execute(
                select(SystemMessage).where(SystemMessage.message_key == message_key)
            )
            message = result.scalar_one_or_none()

            if not message:
                return False

            await session.delete(message)
            await session.commit()
            return True

    async def initialize_default_messages(self) -> int:
        """Initialize database with default messages from messages_ja.py"""
        async with async_session() as session:
            default_messages = [
            {
                "message_key": "MAIN_MENU",
                "message_name": "メインメニュー",
                "category": "menu",
                "content": MAIN_MENU,
                "description": "メインコマンドメニュー画面",
                "variables": "version,time,user_id,handle",
                "is_active": True
            },
            {
                "message_key": "FILE_MENU",
                "message_name": "ファイルボードメニュー",
                "category": "menu",
                "content": FILE_MENU,
                "description": "ファイルボード操作メニュー",
                "variables": "version",
                "is_active": True
            },
            {
                "message_key": "READ_MENU",
                "message_name": "読み取りメニュー",
                "category": "menu",
                "content": READ_MENU,
                "description": "メッセージ読み取りメニュー",
                "variables": "",
                "is_active": True
            },
            {
                "message_key": "INSTALL_MENU",
                "message_name": "インストールメニュー",
                "category": "menu",
                "content": INSTALL_MENU,
                "description": "ユーザ設定メニュー",
                "variables": "",
                "is_active": True
            },
            {
                "message_key": "CHAT_MENU",
                "message_name": "チャットメニュー",
                "category": "menu",
                "content": CHAT_MENU,
                "description": "チャット機能メニュー",
                "variables": "",
                "is_active": True
            },
            {
                "message_key": "SYSOP_MENU",
                "message_name": "SYSOP管理メニュー",
                "category": "menu",
                "content": SYSOP_MENU,
                "description": "システム管理者用メニュー",
                "variables": "",
                "is_active": True
            },
            {
                "message_key": "OPENING_MESSAGE",
                "message_name": "オープニングメッセージ",
                "category": "greeting",
                "content": OPENING_MESSAGE,
                "description": "接続時の挨拶メッセージ",
                "variables": "date,weekday,access_count",
                "is_active": True
            },
            {
                "message_key": "LOGIN_MESSAGE",
                "message_name": "ログインメッセージ",
                "category": "greeting",
                "content": LOGIN_MESSAGE,
                "description": "ログイン成功時のメッセージ",
                "variables": "handle,greeting",
                "is_active": True
            },
            {
                "message_key": "LOGOUT_MESSAGE",
                "message_name": "ログアウトメッセージ",
                "category": "greeting",
                "content": LOGOUT_MESSAGE,
                "description": "ログアウト時のメッセージ",
                "variables": "handle",
                "is_active": True
            },
            {
                "message_key": "HELP_MESSAGE",
                "message_name": "ヘルプメッセージ",
                "category": "help",
                "content": HELP_MESSAGE,
                "description": "コマンドヘルプ画面",
                "variables": "",
                "is_active": True
            },
            {
                "message_key": "SYSINFO_MESSAGE",
                "message_name": "システム情報",
                "category": "info",
                "content": SYSINFO_MESSAGE,
                "description": "ホストシステム情報",
                "variables": "version",
                "is_active": True
            },
            {
                "message_key": "HOST_VERSION",
                "message_name": "バージョン情報",
                "category": "info",
                "content": HOST_VERSION,
                "description": "ホストプログラムバージョン",
                "variables": "version",
                "is_active": True
            },
            {
                "message_key": "CHAT_ROOM_OPENING",
                "message_name": "チャットルーム開始",
                "category": "greeting",
                "content": CHAT_ROOM_OPENING,
                "description": "チャットルーム入室メッセージ",
                "variables": "",
                "is_active": True
            },
            {
                "message_key": "FILE_BOARD_INFO",
                "message_name": "ファイルボード案内",
                "category": "info",
                "content": FILE_BOARD_INFO,
                "description": "ファイルボード利用案内",
                "variables": "",
                "is_active": True
            }
            ]

            count = 0
            for msg_data in default_messages:
                # Check if message already exists
                result = await session.execute(
                    select(SystemMessage).where(
                        SystemMessage.message_key == msg_data["message_key"]
                    )
                )
                existing = result.scalar_one_or_none()

                if not existing:
                    message = SystemMessage(**msg_data)
                    session.add(message)
                    count += 1

            await session.commit()
            return count

    async def get_message_content(self, message_key: str, **kwargs) -> str:
        """Get formatted message content with variable substitution"""
        message = await self.get_message_by_key(message_key)
        if not message or not message.is_active:
            return f"[Message {message_key} not found]"

        try:
            return message.content.format(**kwargs)
        except KeyError as e:
            return f"[Message {message_key} - Missing variable: {e}]"
