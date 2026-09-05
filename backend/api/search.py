from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session
from backend.api.deps import current_user
from backend.core.db import get_db
from backend.models import Message, chat_members

router = APIRouter(prefix="/search", tags=["search"])

@router.get("/messages")
def search(q: str, db: Session = Depends(get_db), u=Depends(current_user)):
    q = q.strip()
    if not q: return []
    ids = [x[0] for x in db.execute(select(chat_members.c.chat_id).where(chat_members.c.user_id == u.id)).all()]
    if not ids: return []
    return db.scalars(select(Message).where(Message.chat_id.in_(ids), Message.text.ilike(f"%{q}%")).order_by(Message.id.desc()).limit(100)).all()
