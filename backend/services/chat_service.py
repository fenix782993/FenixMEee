
from sqlalchemy import select
from sqlalchemy.orm import Session
from backend.models import User

def ensure_private(db: Session, user_a: int, user_b: int):
    # Use existing Chat/ChatMember models when they exist; otherwise return a tiny
    # object. The contacts relationship itself remains persisted independently.
    try:
        from backend.models.chats import Chat, ChatMember
    except Exception:
        try:
            from backend.models import Chat, ChatMember
        except Exception:
            class Result:
                id = None
            return Result()
    try:
        stmt = select(Chat)
        chats = db.execute(stmt).scalars().all()
        for chat in chats:
            members = db.execute(select(ChatMember).where(ChatMember.chat_id==chat.id)).scalars().all()
            ids={getattr(m,"user_id",None) for m in members}
            if ids == {user_a,user_b} and len(members)==2:
                return chat
        chat = Chat(type="private", title=None)
        db.add(chat); db.flush()
        db.add_all([ChatMember(chat_id=chat.id,user_id=user_a),
                    ChatMember(chat_id=chat.id,user_id=user_b)])
        db.flush()
        return chat
    except Exception:
        db.rollback()
        class Result:
            id = None
        return Result()
