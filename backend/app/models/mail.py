"""
Mail Model
"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class Mail(BaseModel):
    """Mail message model"""

    mail_id: Optional[int] = None
    sender_id: str = Field(..., max_length=8)
    sender_handle: str = Field(..., max_length=50)
    recipient_id: str = Field(..., max_length=8)
    subject: str = Field(..., max_length=100)
    body: str = Field(..., max_length=10000)
    sent_at: datetime = Field(default_factory=datetime.now)
    read_at: Optional[datetime] = None
    is_read: bool = False
    is_deleted_by_sender: bool = False
    is_deleted_by_recipient: bool = False

    class Config:
        from_attributes = True


class MailCreate(BaseModel):
    """Mail creation model"""

    sender_id: str = Field(..., max_length=8)
    sender_handle: str = Field(..., max_length=50)
    recipient_id: str = Field(..., max_length=8)
    subject: str = Field(..., max_length=100)
    body: str = Field(..., max_length=10000)


class MailRead(BaseModel):
    """Mail read model"""

    mail_id: int
    sender_id: str
    sender_handle: str
    recipient_id: str
    subject: str
    body: str
    sent_at: datetime
    read_at: Optional[datetime]
    is_read: bool

    class Config:
        from_attributes = True
