"""
Admin API endpoints
"""
from typing import List
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from datetime import datetime

from app.services.user_service import UserService
from app.services.board_service import BoardService
from app.services.message_service import MessageService
from app.protocols.telnet_server import TelnetServer

router = APIRouter()


# Pydantic models
class UserCreate(BaseModel):
    user_id: str
    password: str
    handle_name: str
    email: str | None = None
    level: int = 1


class UserResponse(BaseModel):
    user_id: str
    handle_name: str
    email: str | None
    level: int
    last_login: datetime | None
    created_at: datetime

    class Config:
        from_attributes = True


class BoardCreate(BaseModel):
    board_id: int
    name: str
    description: str | None = None
    read_level: int = 0
    write_level: int = 1


class BoardResponse(BaseModel):
    board_id: int
    name: str
    description: str | None
    read_level: int
    write_level: int
    is_active: bool

    class Config:
        from_attributes = True


class SystemStats(BaseModel):
    active_users: int
    total_users: int
    total_boards: int
    total_messages: int
    telnet_connections: int


class MessageCreate(BaseModel):
    message_key: str
    message_name: str
    category: str
    content: str
    description: str | None = None
    variables: str | None = None
    is_active: bool = True


class MessageUpdate(BaseModel):
    message_name: str | None = None
    category: str | None = None
    content: str | None = None
    description: str | None = None
    variables: str | None = None
    is_active: bool | None = None


class MessageResponse(BaseModel):
    id: int
    message_key: str
    message_name: str
    category: str
    content: str
    description: str | None
    variables: str | None
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# User management
@router.post("/users", response_model=UserResponse)
async def create_user(user_data: UserCreate):
    """Create new user"""
    user_service = UserService()
    try:
        user = await user_service.create_user(
            user_id=user_data.user_id,
            password=user_data.password,
            handle_name=user_data.handle_name,
            email=user_data.email,
            level=user_data.level,
        )
        return user
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/users", response_model=List[UserResponse])
async def get_users(skip: int = 0, limit: int = 100):
    """Get all users"""
    user_service = UserService()
    users = await user_service.get_users(skip=skip, limit=limit)
    return users


@router.get("/users/{user_id}", response_model=UserResponse)
async def get_user(user_id: str):
    """Get user by ID"""
    user_service = UserService()
    user = await user_service.get_user(user_id)

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return user


@router.delete("/users/{user_id}")
async def delete_user(user_id: str):
    """Delete user"""
    user_service = UserService()
    success = await user_service.delete_user(user_id)

    if not success:
        raise HTTPException(status_code=404, detail="User not found")

    return {"message": "User deleted successfully"}


# Board management
@router.post("/boards", response_model=BoardResponse)
async def create_board(board_data: BoardCreate):
    """Create new board"""
    board_service = BoardService()
    try:
        board = await board_service.create_board(
            board_id=board_data.board_id,
            name=board_data.name,
            description=board_data.description,
            read_level=board_data.read_level,
            write_level=board_data.write_level,
        )
        return board
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/boards", response_model=List[BoardResponse])
async def get_boards():
    """Get all boards"""
    board_service = BoardService()
    boards = await board_service.get_boards()
    return boards


@router.get("/boards/{board_id}", response_model=BoardResponse)
async def get_board(board_id: int):
    """Get board by ID"""
    board_service = BoardService()
    board = await board_service.get_board(board_id)

    if not board:
        raise HTTPException(status_code=404, detail="Board not found")

    return board


# System stats
@router.get("/stats", response_model=SystemStats)
async def get_stats():
    """Get system statistics"""
    user_service = UserService()
    board_service = BoardService()

    users = await user_service.get_users()
    boards = await board_service.get_boards()

    # Count total messages
    total_messages = 0
    for board in boards:
        messages = await board_service.get_all_messages(board.board_id)
        total_messages += len(messages)

    # TODO: Get telnet connections from global server instance
    telnet_connections = 0

    return SystemStats(
        active_users=0,  # TODO: Track active sessions
        total_users=len(users),
        total_boards=len(boards),
        total_messages=total_messages,
        telnet_connections=telnet_connections,
    )


# Connection monitoring
@router.get("/connections")
async def get_connections():
    """Get active Telnet connections"""
    # TODO: Access global telnet_server instance
    return {"connections": []}


# Message management
@router.post("/messages", response_model=MessageResponse)
async def create_message(message_data: MessageCreate):
    """Create new system message"""
    message_service = MessageService()
    try:
        message = await message_service.create_message(message_data.model_dump())
        return message
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/messages", response_model=List[MessageResponse])
async def get_messages(category: str | None = None):
    """Get all system messages, optionally filtered by category"""
    message_service = MessageService()
    if category:
        messages = await message_service.get_messages_by_category(category)
    else:
        messages = await message_service.get_all_messages()
    return messages


@router.get("/messages/{message_key}", response_model=MessageResponse)
async def get_message(message_key: str):
    """Get message by key"""
    message_service = MessageService()
    message = await message_service.get_message_by_key(message_key)

    if not message:
        raise HTTPException(status_code=404, detail="Message not found")

    return message


@router.put("/messages/{message_key}", response_model=MessageResponse)
async def update_message(message_key: str, message_data: MessageUpdate):
    """Update existing message"""
    message_service = MessageService()

    # Filter out None values
    update_data = {k: v for k, v in message_data.model_dump().items() if v is not None}

    message = await message_service.update_message(message_key, update_data)

    if not message:
        raise HTTPException(status_code=404, detail="Message not found")

    return message


@router.delete("/messages/{message_key}")
async def delete_message(message_key: str):
    """Delete message"""
    message_service = MessageService()
    success = await message_service.delete_message(message_key)

    if not success:
        raise HTTPException(status_code=404, detail="Message not found")

    return {"message": "Message deleted successfully"}


@router.post("/messages/initialize")
async def initialize_messages():
    """Initialize default messages from messages_ja.py"""
    message_service = MessageService()
    try:
        count = await message_service.initialize_default_messages()
        return {"message": f"Initialized {count} default messages"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
