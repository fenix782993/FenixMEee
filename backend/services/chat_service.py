from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.models.chat import Chat, chat_members


def members(db: Session, chat_id: int) -> list[int]:
    rows = db.execute(
        select(chat_members.c.user_id).where(chat_members.c.chat_id == chat_id)
    ).all()
    return [int(row[0]) for row in rows]


def ensure_private(db: Session, user_a: int, user_b: int) -> Chat:
    """Return an existing 1:1 chat or create it persistently."""
    if user_a == user_b:
        raise ValueError("Private chat requires two different users")

    stmt = (
        select(Chat)
        .where(Chat.kind == "private")
        .join(chat_members, Chat.id == chat_members.c.chat_id)
        .where(chat_members.c.user_id == user_a)
    )
    for chat in db.scalars(stmt).all():
        ids = set(members(db, chat.id))
        if ids == {user_a, user_b}:
            return chat

    chat = Chat(kind="private", title="", username="")
    db.add(chat)
    db.flush()
    db.execute(
        chat_members.insert(),
        [
            {"chat_id": chat.id, "user_id": user_a},
            {"chat_id": chat.id, "user_id": user_b},
        ],
    )
    db.commit()
    db.refresh(chat)
    return chat
