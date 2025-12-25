"""
Board Service - Business logic for message boards
"""
from typing import List, Optional
from datetime import datetime
from sqlalchemy import select, func, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.board import Board, Message, UserReadPosition
from app.core.database import async_session


class BoardService:
    """Board service for message board operations"""

    async def create_board(
        self,
        board_id: int,
        name: str,
        description: Optional[str] = None,
        read_level: int = 0,
        write_level: int = 1,
        enforced_news: bool = False,
        operator_id: Optional[str] = None,
    ) -> Board:
        """Create new board"""
        async with async_session() as session:
            board = Board(
                board_id=board_id,
                name=name,
                description=description,
                read_level=read_level,
                write_level=write_level,
                enforced_news=enforced_news,
                operator_id=operator_id,
            )
            session.add(board)
            await session.commit()
            await session.refresh(board)
            return board

    async def get_board(self, board_id: int) -> Optional[Board]:
        """Get board by ID"""
        async with async_session() as session:
            result = await session.execute(
                select(Board).where(Board.board_id == board_id, Board.is_active == True)
            )
            return result.scalar_one_or_none()

    async def get_boards(self) -> List[Board]:
        """Get all active boards"""
        async with async_session() as session:
            result = await session.execute(
                select(Board).where(Board.is_active == True).order_by(Board.board_id)
            )
            return list(result.scalars().all())

    async def update_board(
        self,
        board_id: int,
        name: Optional[str] = None,
        description: Optional[str] = None,
        read_level: Optional[int] = None,
        write_level: Optional[int] = None,
        is_active: Optional[bool] = None,
        enforced_news: Optional[bool] = None,
        operator_id: Optional[str] = None,
    ) -> Optional[Board]:
        """Update board"""
        async with async_session() as session:
            result = await session.execute(
                select(Board).where(Board.board_id == board_id)
            )
            board = result.scalar_one_or_none()

            if board:
                if name is not None:
                    board.name = name
                if description is not None:
                    board.description = description
                if read_level is not None:
                    board.read_level = read_level
                if write_level is not None:
                    board.write_level = write_level
                if is_active is not None:
                    board.is_active = is_active
                if enforced_news is not None:
                    board.enforced_news = enforced_news
                if operator_id is not None:
                    board.operator_id = operator_id

                board.updated_at = datetime.now()
                await session.commit()
                await session.refresh(board)

            return board

    async def delete_board(self, board_id: int) -> bool:
        """Delete board (soft delete)"""
        board = await self.update_board(board_id, is_active=False)
        return board is not None

    async def create_message(
        self,
        board_id: int,
        user_id: str,
        handle_name: str,
        title: str,
        body: str,
        parent_id: Optional[int] = None,
    ) -> Message:
        """Create new message"""
        async with async_session() as session:
            # Get board
            board_result = await session.execute(
                select(Board).where(Board.board_id == board_id)
            )
            board = board_result.scalar_one_or_none()

            if not board:
                raise ValueError(f"Board {board_id} not found")

            # Get next message number
            max_no_result = await session.execute(
                select(func.max(Message.message_no)).where(Message.board_id == board.id)
            )
            max_no = max_no_result.scalar() or 0

            message = Message(
                message_no=max_no + 1,
                board_id=board.id,
                user_id=user_id,
                handle_name=handle_name,
                title=title,
                body=body,
                parent_id=parent_id,
            )

            session.add(message)
            await session.commit()
            await session.refresh(message)

            return message

    async def get_message(self, board_id: int, message_no: int) -> Optional[Message]:
        """Get message by board_id and message_no"""
        async with async_session() as session:
            result = await session.execute(
                select(Message)
                .join(Board)
                .where(
                    and_(
                        Board.board_id == board_id,
                        Message.message_no == message_no
                    )
                )
            )
            return result.scalar_one_or_none()

    async def get_recent_messages(
        self, board_id: int, limit: int = 20, skip: int = 0
    ) -> List[Message]:
        """Get recent messages from board (excludes deleted)"""
        async with async_session() as session:
            board_result = await session.execute(
                select(Board).where(Board.board_id == board_id)
            )
            board = board_result.scalar_one_or_none()

            if not board:
                return []

            result = await session.execute(
                select(Message)
                .where(
                    and_(
                        Message.board_id == board.id,
                        Message.deleted == False
                    )
                )
                .order_by(Message.message_no.desc())
                .offset(skip)
                .limit(limit)
            )
            return list(result.scalars().all())

    async def get_all_messages(self, board_id: int) -> List[Message]:
        """Get all messages from board (excludes deleted)"""
        async with async_session() as session:
            board_result = await session.execute(
                select(Board).where(Board.board_id == board_id)
            )
            board = board_result.scalar_one_or_none()

            if not board:
                return []

            result = await session.execute(
                select(Message)
                .where(
                    and_(
                        Message.board_id == board.id,
                        Message.deleted == False
                    )
                )
                .order_by(Message.message_no)
            )
            return list(result.scalars().all())

    async def get_unread_messages(self, board_id: int, user_id: str) -> List[Message]:
        """Get unread messages from board for user"""
        async with async_session() as session:
            board_result = await session.execute(
                select(Board).where(Board.board_id == board_id)
            )
            board = board_result.scalar_one_or_none()

            if not board:
                return []

            # Get user's last read position
            last_read = await self.get_read_position(user_id, board_id)

            # Get messages after last read position (excluding deleted)
            result = await session.execute(
                select(Message)
                .where(
                    and_(
                        Message.board_id == board.id,
                        Message.message_no > last_read,
                        Message.deleted == False
                    )
                )
                .order_by(Message.message_no)
            )
            return list(result.scalars().all())

    async def delete_message(self, board_id: int, message_no: int, deleted_by: str) -> bool:
        """Soft delete message"""
        async with async_session() as session:
            result = await session.execute(
                select(Message)
                .join(Board)
                .where(
                    and_(
                        Board.board_id == board_id,
                        Message.message_no == message_no
                    )
                )
            )
            message = result.scalar_one_or_none()

            if message:
                message.deleted = True
                message.deleted_at = datetime.now()
                message.deleted_by = deleted_by
                await session.commit()
                return True

            return False

    async def get_new_message_count(self, board_id: int, user_id: str) -> int:
        """Get count of new messages since user's last read"""
        async with async_session() as session:
            board_result = await session.execute(
                select(Board).where(Board.board_id == board_id)
            )
            board = board_result.scalar_one_or_none()

            if not board:
                return 0

            # Get user's last read position
            last_read = await self.get_read_position(user_id, board_id)

            # Count messages after last read position (excluding deleted)
            result = await session.execute(
                select(func.count()).where(
                    and_(
                        Message.board_id == board.id,
                        Message.message_no > last_read,
                        Message.deleted == False
                    )
                )
            )
            return result.scalar() or 0

    async def search_messages(
        self, board_id: int, keyword: str, limit: int = 50
    ) -> List[Message]:
        """Search messages by keyword"""
        async with async_session() as session:
            board_result = await session.execute(
                select(Board).where(Board.board_id == board_id)
            )
            board = board_result.scalar_one_or_none()

            if not board:
                return []

            result = await session.execute(
                select(Message)
                .where(
                    and_(
                        Message.board_id == board.id,
                        or_(
                            Message.title.contains(keyword),
                            Message.body.contains(keyword)
                        )
                    )
                )
                .order_by(Message.created_at.desc())
                .limit(limit)
            )
            return list(result.scalars().all())

    async def restore_message(self, board_id: int, message_no: int) -> bool:
        """Restore soft-deleted message"""
        async with async_session() as session:
            result = await session.execute(
                select(Message)
                .join(Board)
                .where(
                    and_(
                        Board.board_id == board_id,
                        Message.message_no == message_no,
                        Message.deleted == True
                    )
                )
            )
            message = result.scalar_one_or_none()

            if message:
                message.deleted = False
                message.deleted_at = None
                message.deleted_by = None
                await session.commit()
                return True

            return False

    async def update_read_position(
        self,
        user_id: str,
        board_id: int,
        message_no: int
    ) -> None:
        """Update user's read position on a board"""
        async with async_session() as session:
            # Get board internal ID
            board_result = await session.execute(
                select(Board).where(Board.board_id == board_id)
            )
            board = board_result.scalar_one_or_none()

            if not board:
                return

            # Check if position exists
            result = await session.execute(
                select(UserReadPosition).where(
                    and_(
                        UserReadPosition.user_id == user_id,
                        UserReadPosition.board_id == board.id
                    )
                )
            )
            position = result.scalar_one_or_none()

            if position:
                # Update existing
                if message_no > position.last_read_message_no:
                    position.last_read_message_no = message_no
                    position.last_read_at = datetime.now()
            else:
                # Create new
                position = UserReadPosition(
                    user_id=user_id,
                    board_id=board.id,
                    last_read_message_no=message_no,
                    last_read_at=datetime.now()
                )
                session.add(position)

            await session.commit()

    async def get_read_position(
        self,
        user_id: str,
        board_id: int
    ) -> int:
        """Get user's last read message number"""
        async with async_session() as session:
            board_result = await session.execute(
                select(Board).where(Board.board_id == board_id)
            )
            board = board_result.scalar_one_or_none()

            if not board:
                return 0

            result = await session.execute(
                select(UserReadPosition).where(
                    and_(
                        UserReadPosition.user_id == user_id,
                        UserReadPosition.board_id == board.id
                    )
                )
            )
            position = result.scalar_one_or_none()

            return position.last_read_message_no if position else 0

    async def get_enforced_news_boards(self) -> List[Board]:
        """Get all boards with enforced_news flag"""
        async with async_session() as session:
            result = await session.execute(
                select(Board).where(
                    and_(
                        Board.is_active == True,
                        Board.enforced_news == True
                    )
                ).order_by(Board.board_id)
            )
            return list(result.scalars().all())
