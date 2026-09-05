from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.api.deps import current_user
from backend.core.db import get_db
from backend.models import Chat, User, chat_members
from backend.schemas.chat import PrivateChatIn, GroupCreateIn, ChatOut
from backend.services.chat_service import ensure_private, members

router = APIRouter(prefix="/chats", tags=["chats"])

def present_chat(db: Session, chat: Chat, uid: int) -> dict:
    ids = members(db, chat.id)
    other = None
    if chat.kind == "private":
        other_id = next((x for x in ids if x != uid), None)
        other = db.get(User, other_id) if other_id else None
    return {
        "id": chat.id,
        "kind": chat.kind,
        "title": chat.title or (other.display_name if other else "Чат"),
        "username": chat.username or (other.username if other else ""),
        "description": chat.description or (other.bio if other else ""),
        "avatar": chat.avatar or (other.avatar if other else None),
    }

@router.get("", response_model=list[ChatOut])
def chats(db: Session = Depends(get_db), u=Depends(current_user)):
    ids = [x[0] for x in db.execute(select(chat_members.c.chat_id).where(chat_members.c.user_id == u.id)).all()]
    if not ids:
        return []
    rows = db.scalars(select(Chat).where(Chat.id.in_(ids)).order_by(Chat.id.desc())).all()
    return [present_chat(db, chat, u.id) for chat in rows]


@router.get("/saved", response_model=ChatOut)
def saved(db: Session = Depends(get_db), u=Depends(current_user)):
    chat = db.scalar(select(Chat).join(chat_members, Chat.id==chat_members.c.chat_id).where(Chat.kind=="saved", chat_members.c.user_id==u.id))
    if not chat:
        chat=Chat(kind="saved",title="Избранное",description="Личные сохранённые сообщения")
        db.add(chat); db.flush(); db.execute(chat_members.insert().values(chat_id=chat.id,user_id=u.id)); db.commit(); db.refresh(chat)
    return present_chat(db,chat,u.id)

@router.post("/private", response_model=ChatOut)
def private(data: PrivateChatIn, db: Session = Depends(get_db), u=Depends(current_user)):
    if data.other_user_id == u.id or not db.get(User, data.other_user_id):
        raise HTTPException(404, "User not found")
    return present_chat(db, ensure_private(db, u.id, data.other_user_id), u.id)

@router.post("/group", response_model=ChatOut)
def group(data: GroupCreateIn, db: Session = Depends(get_db), u=Depends(current_user)):
    chat = Chat(kind="group", title=data.title, description=data.description)
    db.add(chat)
    db.flush()
    ids = set(data.member_ids) | {u.id}
    db.execute(chat_members.insert(), [{"chat_id": chat.id, "user_id": x} for x in ids if db.get(User, x)])
    db.commit()
    db.refresh(chat)
    return present_chat(db, chat, u.id)

@router.get("/{chat_id}/members")
def chat_members_list(chat_id: int, db: Session = Depends(get_db), u=Depends(current_user)):
    if u.id not in members(db, chat_id):
        raise HTTPException(403, "Not a member")
    return [db.get(User, i) for i in members(db, chat_id)]
