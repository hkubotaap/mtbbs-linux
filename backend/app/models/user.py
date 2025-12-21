"""
User model
"""
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text
from sqlalchemy.sql import func
from app.core.database import Base


class User(Base):
    """User model"""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String(8), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    handle_name = Column(String(14), nullable=False)
    email = Column(String(255), nullable=True)
    level = Column(Integer, default=1)  # -1 to 9

    # Profile
    name = Column(String(50), nullable=True)
    address = Column(Text, nullable=True)
    tel = Column(String(20), nullable=True)
    hobby = Column(Text, nullable=True)
    birthday = Column(String(10), nullable=True)
    comment = Column(Text, nullable=True)
    memo = Column(String(25), nullable=True)

    # Settings
    use_login_report = Column(Boolean, default=True)
    receive_telegram_bell = Column(Boolean, default=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    last_login = Column(DateTime(timezone=True), nullable=True)
    last_read_date = Column(DateTime(timezone=True), nullable=True)

    # Status
    is_active = Column(Boolean, default=True)
    is_banned = Column(Boolean, default=False)

    def __repr__(self):
        return f"<User {self.user_id} ({self.handle_name})>"
