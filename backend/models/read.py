from sqlalchemy import ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from backend.core.db import Base
class ReadState(Base):
    __tablename__ = "read_states"
    __table_args__ = (UniqueConstraint("chat_id", "user_id"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    chat_id: Mapped[int] = mapped_column(ForeignKey("chats.id"))
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    last_message_id: Mapped[int] = mapped_column(default=0)
