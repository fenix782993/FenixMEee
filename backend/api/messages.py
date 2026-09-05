from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session
from backend.api.deps import current_user
from backend.core.db import get_db
from backend.models import Message, Reaction
from backend.schemas.message import MessageCreate, MessageUpdate, ReactionIn, MessageOut
from backend.services.chat_service import members
from backend.services.ws import manager

router = APIRouter(prefix="/chats/{chat_id}/messages", tags=["messages"])

def check(db, chat_id, user):
    if user.id not in members(db, chat_id):
        raise HTTPException(403, "Not a member")

def out(m):
    return MessageOut.model_validate(m, from_attributes=True)

@router.get("", response_model=list[MessageOut])
def history(chat_id: int, limit: int = 100, db: Session = Depends(get_db), u=Depends(current_user)):
    check(db, chat_id, u)
    limit = max(1, min(limit, 200))
    return list(reversed(db.scalars(select(Message).where(Message.chat_id == chat_id).order_by(Message.id.desc()).limit(limit)).all()))

@router.post("", response_model=MessageOut)
async def send(chat_id: int, data: MessageCreate, db: Session = Depends(get_db), u=Depends(current_user)):
    check(db, chat_id, u)
    if not data.text.strip() and not data.media_url:
        raise HTTPException(400, "Message is empty")
    m = Message(chat_id=chat_id, sender_id=u.id, **data.model_dump())
    db.add(m); db.commit(); db.refresh(m)
    payload = out(m).model_dump(mode="json")
    await manager.broadcast(chat_id, {"type": "message", "message": payload})
    return m

@router.patch("/{message_id}", response_model=MessageOut)
async def edit(chat_id: int, message_id: int, data: MessageUpdate, db: Session = Depends(get_db), u=Depends(current_user)):
    check(db, chat_id, u)
    m = db.get(Message, message_id)
    if not m or m.chat_id != chat_id or m.sender_id != u.id or m.deleted:
        raise HTTPException(404, "Message not found")
    m.text = data.text; m.edited = True
    db.commit(); db.refresh(m)
    await manager.broadcast(chat_id, {"type": "message_updated", "message": out(m).model_dump(mode="json")})
    return m

@router.delete("/{message_id}")
async def delete(chat_id: int, message_id: int, db: Session = Depends(get_db), u=Depends(current_user)):
    check(db, chat_id, u)
    m = db.get(Message, message_id)
    if not m or m.chat_id != chat_id or m.sender_id != u.id:
        raise HTTPException(404, "Message not found")
    m.deleted = True; m.text = ""
    db.commit()
    await manager.broadcast(chat_id, {"type": "message_deleted", "message_id": message_id})
    return {"ok": True}

@router.post("/{message_id}/reaction")
async def reaction(chat_id: int, message_id: int, data: ReactionIn, db: Session = Depends(get_db), u=Depends(current_user)):
    check(db, chat_id, u)
    m = db.get(Message, message_id)
    if not m or m.chat_id != chat_id: raise HTTPException(404, "Message not found")
    r = db.scalar(select(Reaction).where(Reaction.message_id == message_id, Reaction.user_id == u.id, Reaction.emoji == data.emoji))
    if r: db.delete(r)
    else: db.add(Reaction(message_id=message_id, user_id=u.id, emoji=data.emoji))
    db.commit()
    await manager.broadcast(chat_id, {"type": "reaction", "message_id": message_id, "emoji": data.emoji, "user_id": u.id})
    return {"ok": True}

@router.post("/{message_id}/pin")
async def pin(chat_id: int, message_id: int, db: Session = Depends(get_db), u=Depends(current_user)):
    check(db, chat_id, u)
    m = db.get(Message, message_id)
    if not m or m.chat_id != chat_id: raise HTTPException(404, "Message not found")
    m.pinned = not m.pinned; db.commit()
    await manager.broadcast(chat_id, {"type": "pin", "message_id": message_id, "pinned": m.pinned})
    return {"pinned": m.pinned}
