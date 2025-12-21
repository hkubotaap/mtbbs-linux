# -*- coding: utf-8 -*-
"""
System Message Model - Customizable BBS Messages
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime
from app.core.database import Base


class SystemMessage(Base):
    """System messages for telnet BBS interface"""
    __tablename__ = "system_messages"

    id = Column(Integer, primary_key=True, index=True)
    message_key = Column(String(50), unique=True, nullable=False, index=True)
    message_name = Column(String(100), nullable=False)
    category = Column(String(20), nullable=False, index=True)  # menu, greeting, info, help
    content = Column(Text, nullable=False)
    description = Column(String(255), nullable=True)
    variables = Column(String(255), nullable=True)  # comma-separated list of template variables
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    def __repr__(self):
        return f"<SystemMessage(key={self.message_key}, name={self.message_name})>"
