from datetime import datetime, timezone
from sqlalchemy import DateTime, ForeignKey, String, Text, Boolean, Table, Column
from sqlalchemy.orm import Mapped, mapped_column
from backend.core.db import Base

chat_members = Table("chat_members", Base.metadata,
    Column("chat_id", ForeignKey("chats.id"), primary_key=True),
    Column("user_id", ForeignKey("users.id"), primary_key=True),
)

class Chat(Base):
    __tablename__ = "chats"
    id: Mapped[int] = mapped_column(primary_key=True)
    kind: Mapped[str] = mapped_column(String(20), default="private")
    title: Mapped[str] = mapped_column(String(120), default="")
    username: Mapped[str] = mapped_column(String(64), default="")
    description: Mapped[str] = mapped_column(Text, default="")
    avatar: Mapped[str | None] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))
    is_public: Mapped[bool] = mapped_column(Boolean, default=False)
