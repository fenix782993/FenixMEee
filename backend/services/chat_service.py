from sqlalchemy import select, or_, and_
from sqlalchemy.orm import Session
from backend.models import Chat, User, chat_members

def ensure_private(db: Session, a: int, b: int):
    q = select(Chat).where(Chat.kind=="private").join(chat_members, Chat.id==chat_members.c.chat_id).where(chat_members.c.user_id==a)
    for chat in db.scalars(q).all():
        members = {x[0] for x in db.execute(select(chat_members.c.user_id).where(chat_members.c.chat_id==chat.id)).all()}
        if members == {a,b}: return chat
    chat=Chat(kind="private", title="", username="")
    db.add(chat); db.flush()
    db.execute(chat_members.insert(), [{"chat_id":chat.id,"user_id":a},{"chat_id":chat.id,"user_id":b}])
    db.commit(); db.refresh(chat); return chat

def members(db, chat_id):
    return [r[0] for r in db.execute(select(chat_members.c.user_id).where(chat_members.c.chat_id==chat_id)).all()]
