#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Update MAIN_MENU in database
"""
import asyncio
import sys
from pathlib import Path

# Add parent directory to path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from app.core.database import async_session
from app.models.system_message import SystemMessage
from app.resources.messages_ja import MAIN_MENU
from sqlalchemy import select


async def update_main_menu():
    """Update MAIN_MENU content in database"""
    async with async_session() as session:
        result = await session.execute(
            select(SystemMessage).where(SystemMessage.message_key == "MAIN_MENU")
        )
        message = result.scalar_one_or_none()

        if message:
            message.content = MAIN_MENU
            await session.commit()
            print("✓ MAIN_MENU updated successfully")
        else:
            print("✗ MAIN_MENU not found in database")


if __name__ == "__main__":
    asyncio.run(update_main_menu())
