from datetime import datetime, timezone
from sqlalchemy import DateTime, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from backend.core.db import Base
class UserSettings(Base):
    __tablename__='user_settings'
    id: Mapped[int]=mapped_column(primary_key=True)
    user_id: Mapped[int]=mapped_column(ForeignKey('users.id'),unique=True)
    theme: Mapped[str]=mapped_column(String(20),default='system')
    language: Mapped[str]=mapped_column(String(10),default='ru')
    notifications: Mapped[bool]=mapped_column(default=True)
    sounds: Mapped[bool]=mapped_column(default=True)
    dnd: Mapped[bool]=mapped_column(default=False)
    privacy: Mapped[str]=mapped_column(Text,default='everyone')
    updated_at: Mapped[datetime]=mapped_column(DateTime,default=lambda:datetime.now(timezone.utc),onupdate=lambda:datetime.now(timezone.utc))
