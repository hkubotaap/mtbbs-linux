#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Check message encoding in database
"""
import asyncio
import sys
from pathlib import Path

backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from app.core.database import async_session
from app.models.board import Message, Board
from sqlalchemy import select


async def check_latest_message():
    """Check latest message encoding"""
    async with async_session() as session:
        # Get board
        board_result = await session.execute(
            select(Board).where(Board.board_id == 99)
        )
        board = board_result.scalar_one_or_none()

        if not board:
            print("Board 99 not found")
            return

        # Get latest message
        result = await session.execute(
            select(Message)
            .where(Message.board_id == board.id)
            .order_by(Message.message_no.desc())
            .limit(1)
        )
        message = result.scalar_one_or_none()

        if not message:
            print("No messages found")
            return

        print(f"Message #{message.message_no}")
        print(f"Title: {message.title!r}")
        print(f"Title bytes: {message.title.encode('utf-8').hex()}")
        print(f"\nBody: {message.body!r}")
        print(f"Body bytes: {message.body.encode('utf-8').hex()}")


if __name__ == "__main__":
    asyncio.run(check_latest_message())
