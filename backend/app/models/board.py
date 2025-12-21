"""
Board and Message models
"""
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Boolean
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base


class Board(Base):
    """Message board"""
    __tablename__ = "boards"

    id = Column(Integer, primary_key=True, index=True)
    board_id = Column(Integer, unique=True, index=True, nullable=False)
    name = Column(String(50), nullable=False)
    description = Column(Text, nullable=True)

    # Access control
    read_level = Column(Integer, default=0)  # Minimum level to read
    write_level = Column(Integer, default=1)  # Minimum level to write

    # Settings
    is_active = Column(Boolean, default=True)
    max_messages = Column(Integer, default=1000)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    messages = relationship("Message", back_populates="board", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Board {self.board_id}: {self.name}>"


class Message(Base):
    """Board message"""
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True)
    message_no = Column(Integer, nullable=False)  # Sequential number within board
    board_id = Column(Integer, ForeignKey("boards.id"), nullable=False)

    # Author
    user_id = Column(String(8), ForeignKey("users.user_id"), nullable=False)
    handle_name = Column(String(14), nullable=False)

    # Content
    title = Column(String(100), nullable=False)
    body = Column(Text, nullable=False)

    # Response chain
    parent_id = Column(Integer, ForeignKey("messages.id"), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    board = relationship("Board", back_populates="messages")
    responses = relationship("Message", back_populates="parent", remote_side=[id])
    parent = relationship("Message", back_populates="responses", remote_side=[parent_id])

    def __repr__(self):
        return f"<Message {self.message_no} on Board {self.board_id}: {self.title}>"
