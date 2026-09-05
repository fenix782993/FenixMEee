from datetime import datetime, timezone
from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from backend.core.db import Base

class Block(Base):
    __tablename__='blocks'
    id: Mapped[int]=mapped_column(primary_key=True)
    user_id: Mapped[int]=mapped_column(ForeignKey('users.id'),index=True)
    blocked_user_id: Mapped[int]=mapped_column(ForeignKey('users.id'),index=True)
    created_at: Mapped[datetime]=mapped_column(DateTime,default=lambda:datetime.now(timezone.utc))
    __table_args__=(UniqueConstraint('user_id','blocked_user_id',name='uq_block'),)

class Draft(Base):
    __tablename__='drafts'
    id: Mapped[int]=mapped_column(primary_key=True)
    user_id: Mapped[int]=mapped_column(ForeignKey('users.id'),index=True)
    chat_id: Mapped[int]=mapped_column(ForeignKey('chats.id'),index=True)
    text: Mapped[str]=mapped_column(Text,default='')
    updated_at: Mapped[datetime]=mapped_column(DateTime,default=lambda:datetime.now(timezone.utc),onupdate=lambda:datetime.now(timezone.utc))
    __table_args__=(UniqueConstraint('user_id','chat_id',name='uq_draft'),)

class GroupAdmin(Base):
    __tablename__='group_admins'
    id: Mapped[int]=mapped_column(primary_key=True)
    chat_id: Mapped[int]=mapped_column(ForeignKey('chats.id'),index=True)
    user_id: Mapped[int]=mapped_column(ForeignKey('users.id'),index=True)
    can_manage: Mapped[bool]=mapped_column(Boolean,default=True)
    can_delete: Mapped[bool]=mapped_column(Boolean,default=True)
    can_ban: Mapped[bool]=mapped_column(Boolean,default=True)
    can_pin: Mapped[bool]=mapped_column(Boolean,default=True)
    __table_args__=(UniqueConstraint('chat_id','user_id',name='uq_group_admin'),)

class CallSession(Base):
    __tablename__='call_sessions'
    id: Mapped[int]=mapped_column(primary_key=True)
    chat_id: Mapped[int|None]=mapped_column(ForeignKey('chats.id'),nullable=True)
    caller_id: Mapped[int]=mapped_column(ForeignKey('users.id'))
    callee_id: Mapped[int]=mapped_column(ForeignKey('users.id'))
    kind: Mapped[str]=mapped_column(String(20),default='audio')
    status: Mapped[str]=mapped_column(String(20),default='ringing')
    offer: Mapped[str|None]=mapped_column(Text,nullable=True)
    answer: Mapped[str|None]=mapped_column(Text,nullable=True)
    created_at: Mapped[datetime]=mapped_column(DateTime,default=lambda:datetime.now(timezone.utc))
    ended_at: Mapped[datetime|None]=mapped_column(DateTime,nullable=True)
