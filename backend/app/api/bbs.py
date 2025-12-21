"""
BBS API endpoints (for web/mobile clients)
"""
from typing import List
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from datetime import datetime

from app.services.board_service import BoardService

router = APIRouter()


class MessageResponse(BaseModel):
    message_no: int
    user_id: str
    handle_name: str
    title: str
    body: str
    created_at: datetime

    class Config:
        from_attributes = True


class MessageCreate(BaseModel):
    board_id: int
    title: str
    body: str
    parent_id: int | None = None


@router.get("/boards")
async def list_boards():
    """List all boards"""
    board_service = BoardService()
    boards = await board_service.get_boards()
    return [
        {
            "board_id": board.board_id,
            "name": board.name,
            "description": board.description,
        }
        for board in boards
    ]


@router.get("/boards/{board_id}/messages", response_model=List[MessageResponse])
async def get_board_messages(board_id: int, skip: int = 0, limit: int = 20):
    """Get messages from a board"""
    board_service = BoardService()
    messages = await board_service.get_recent_messages(board_id, limit=limit, skip=skip)
    return messages


@router.get("/boards/{board_id}/messages/{message_no}", response_model=MessageResponse)
async def get_message(board_id: int, message_no: int):
    """Get specific message"""
    board_service = BoardService()
    message = await board_service.get_message(board_id, message_no)

    if not message:
        raise HTTPException(status_code=404, detail="Message not found")

    return message


@router.post("/messages", response_model=MessageResponse)
async def create_message(message_data: MessageCreate, user_id: str = "web", handle_name: str = "WebUser"):
    """Create new message"""
    board_service = BoardService()

    try:
        message = await board_service.create_message(
            board_id=message_data.board_id,
            user_id=user_id,
            handle_name=handle_name,
            title=message_data.title,
            body=message_data.body,
            parent_id=message_data.parent_id,
        )
        return message
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
