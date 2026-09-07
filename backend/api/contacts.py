
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from backend.api.deps import current_user
from backend.core.db import get_db
from backend.models import User, Contact, FriendRequest, Block
from backend.services.chat_service import ensure_private

router = APIRouter(prefix="/contacts", tags=["contacts"])

class UserOut(BaseModel):
    id: int
    username: str | None = None
    display_name: str | None = None
    avatar_url: str | None = None

    model_config = {"from_attributes": True}

class ContactAction(BaseModel):
    user_id: int

def _uid(user):
    return int(getattr(user, "id"))

@router.get("", response_model=list[UserOut])
def list_contacts(db: Session = Depends(get_db), user=Depends(current_user)):
    uid = _uid(user)
    rows = db.execute(select(Contact).where(Contact.owner_id == uid)).scalars().all()
    ids = [r.contact_id for r in rows]
    if not ids:
        return []
    return db.execute(select(User).where(User.id.in_(ids))).scalars().all()

@router.get("/search", response_model=list[UserOut])
def search_people(q: str, db: Session = Depends(get_db), user=Depends(current_user)):
    q = q.strip()
    if not q:
        return []
    like = f"%{q}%"
    stmt = select(User).where(
        User.id != _uid(user),
        or_(
            User.username.ilike(like),
            User.display_name.ilike(like),
        )
    ).limit(30)
    return db.execute(stmt).scalars().all()

@router.get("/requests/incoming")
def incoming_requests(db: Session = Depends(get_db), user=Depends(current_user)):
    rows = db.execute(
        select(FriendRequest).where(
            FriendRequest.receiver_id == _uid(user),
            FriendRequest.status == "pending"
        )
    ).scalars().all()
    result=[]
    for r in rows:
        u=db.get(User,r.sender_id)
        if u: result.append({"id":r.id,"user":UserOut.model_validate(u).model_dump()})
    return result

@router.get("/requests/outgoing")
def outgoing_requests(db: Session = Depends(get_db), user=Depends(current_user)):
    rows = db.execute(
        select(FriendRequest).where(
            FriendRequest.sender_id == _uid(user),
            FriendRequest.status == "pending"
        )
    ).scalars().all()
    result=[]
    for r in rows:
        u=db.get(User,r.receiver_id)
        if u: result.append({"id":r.id,"user":UserOut.model_validate(u).model_dump()})
    return result

@router.post("/request")
def send_request(payload: ContactAction, db: Session = Depends(get_db), user=Depends(current_user)):
    uid=_uid(user); target=payload.user_id
    if uid == target:
        raise HTTPException(400,"Нельзя добавить самого себя")
    if not db.get(User,target):
        raise HTTPException(404,"Пользователь не найден")
    blocked=db.execute(select(Block).where(
        or_(
            (Block.owner_id==uid)&(Block.blocked_id==target),
            (Block.owner_id==target)&(Block.blocked_id==uid)
        )
    )).scalar_one_or_none()
    if blocked:
        raise HTTPException(403,"Добавление недоступно")
    exists=db.execute(select(Contact).where(Contact.owner_id==uid,Contact.contact_id==target)).scalar_one_or_none()
    if exists:
        return {"status":"already_contact"}
    reverse=db.execute(select(FriendRequest).where(
        FriendRequest.sender_id==target, FriendRequest.receiver_id==uid, FriendRequest.status=="pending"
    )).scalar_one_or_none()
    if reverse:
        reverse.status="accepted"
        db.add_all([Contact(owner_id=uid,contact_id=target),Contact(owner_id=target,contact_id=uid)])
        db.commit()
        chat=ensure_private(db,uid,target)
        return {"status":"accepted","chat_id":getattr(chat,"id",None)}
    req=db.execute(select(FriendRequest).where(
        FriendRequest.sender_id==uid, FriendRequest.receiver_id==target
    )).scalar_one_or_none()
    if req:
        req.status="pending"
    else:
        req=FriendRequest(sender_id=uid,receiver_id=target,status="pending")
        db.add(req)
    db.commit()
    return {"status":"pending","request_id":req.id}

@router.post("/request/{request_id}/accept")
def accept_request(request_id:int, db:Session=Depends(get_db), user=Depends(current_user)):
    req=db.get(FriendRequest,request_id)
    if not req or req.receiver_id != _uid(user) or req.status!="pending":
        raise HTTPException(404,"Запрос не найден")
    req.status="accepted"
    db.add_all([Contact(owner_id=req.sender_id,contact_id=req.receiver_id),
                Contact(owner_id=req.receiver_id,contact_id=req.sender_id)])
    chat=ensure_private(db,req.sender_id,req.receiver_id)
    db.commit()
    return {"status":"accepted","chat_id":getattr(chat,"id",None)}

@router.post("/request/{request_id}/decline")
def decline_request(request_id:int, db:Session=Depends(get_db), user=Depends(current_user)):
    req=db.get(FriendRequest,request_id)
    if not req or req.receiver_id != _uid(user):
        raise HTTPException(404,"Запрос не найден")
    req.status="declined"
    db.commit()
    return {"status":"declined"}

@router.delete("/{contact_id}")
def remove_contact(contact_id:int, db:Session=Depends(get_db), user=Depends(current_user)):
    uid=_uid(user)
    rows=db.execute(select(Contact).where(Contact.owner_id==uid,Contact.contact_id==contact_id)).scalars().all()
    for row in rows: db.delete(row)
    db.commit()
    return {"status":"removed"}
