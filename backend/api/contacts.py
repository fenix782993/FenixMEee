from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select, or_, and_, delete
from sqlalchemy.orm import Session
from backend.api.deps import current_user
from backend.core.db import get_db
from backend.models import User, Contact, FriendRequest, Block
from backend.services.chat_service import ensure_private

router = APIRouter(prefix='/contacts', tags=['contacts'])

class ContactIn(BaseModel):
    user_id: int
    nickname: str = Field(default='', max_length=80)
class RequestIn(BaseModel):
    user_id: int
class RespondIn(BaseModel):
    request_id: int
    accept: bool


def person(u, nickname=''):
    return {'id':u.id,'public_code':u.public_code,'username':u.username,'display_name':u.display_name,'nickname':nickname,'avatar':u.avatar,'bio':u.bio,'online':u.online,'last_seen':u.last_seen,'role':u.role}

def is_blocked(db, a, b):
    return bool(db.scalar(select(Block).where(Block.user_id==a, Block.blocked_user_id==b))) or bool(db.scalar(select(Block).where(Block.user_id==b, Block.blocked_user_id==a)))

@router.get('')
def list_contacts(db: Session=Depends(get_db), u=Depends(current_user)):
    rows = db.scalars(select(Contact).where(Contact.owner_id==u.id).order_by(Contact.id.desc())).all()
    out=[]
    for c in rows:
        target=db.get(User,c.contact_user_id)
        if target: out.append(person(target,c.nickname))
    return out

@router.post('')
def add_contact(data: ContactIn, db: Session=Depends(get_db), u=Depends(current_user)):
    if data.user_id == u.id: raise HTTPException(400,'Нельзя добавить себя')
    target=db.get(User,data.user_id)
    if not target: raise HTTPException(404,'Пользователь не найден')
    if is_blocked(db,u.id,target.id): raise HTTPException(403,'Контакт заблокирован')
    c=db.scalar(select(Contact).where(Contact.owner_id==u.id,Contact.contact_user_id==target.id))
    if not c:
        c=Contact(owner_id=u.id,contact_user_id=target.id,nickname=data.nickname.strip())
        db.add(c); db.commit(); db.refresh(c)
    return person(target,c.nickname)

@router.patch('/{user_id}')
def rename_contact(user_id:int,data:ContactIn,db:Session=Depends(get_db),u=Depends(current_user)):
    c=db.scalar(select(Contact).where(Contact.owner_id==u.id,Contact.contact_user_id==user_id))
    if not c: raise HTTPException(404,'Контакт не найден')
    c.nickname=data.nickname.strip(); db.commit(); return {'ok':True}

@router.delete('/{user_id}')
def remove_contact(user_id:int,db:Session=Depends(get_db),u=Depends(current_user)):
    db.execute(delete(Contact).where(Contact.owner_id==u.id,Contact.contact_user_id==user_id)); db.commit(); return {'ok':True}

@router.get('/requests')
def requests(db:Session=Depends(get_db),u=Depends(current_user)):
    incoming=db.scalars(select(FriendRequest).where(FriendRequest.receiver_id==u.id,FriendRequest.status=='pending').order_by(FriendRequest.id.desc())).all()
    outgoing=db.scalars(select(FriendRequest).where(FriendRequest.sender_id==u.id,FriendRequest.status=='pending').order_by(FriendRequest.id.desc())).all()
    return {'incoming':[{'id':r.id,'from':person(db.get(User,r.sender_id)),'created_at':r.created_at} for r in incoming], 'outgoing':[{'id':r.id,'to':person(db.get(User,r.receiver_id)),'created_at':r.created_at} for r in outgoing]}

@router.post('/request')
def send_request(data:RequestIn,db:Session=Depends(get_db),u=Depends(current_user)):
    target=db.get(User,data.user_id)
    if not target or target.id==u.id: raise HTTPException(404,'Пользователь не найден')
    if is_blocked(db,u.id,target.id): raise HTTPException(403,'Нельзя отправить запрос этому пользователю')
    if db.scalar(select(Contact).where(Contact.owner_id==u.id,Contact.contact_user_id==target.id)):
        return {'ok':True,'status':'already_contact'}
    reverse=db.scalar(select(FriendRequest).where(FriendRequest.sender_id==target.id,FriendRequest.receiver_id==u.id,FriendRequest.status=='pending'))
    if reverse:
        reverse.status='accepted'; reverse.responded_at=datetime.now(timezone.utc)
        for a,b in ((u.id,target.id),(target.id,u.id)):
            if not db.scalar(select(Contact).where(Contact.owner_id==a,Contact.contact_user_id==b)): db.add(Contact(owner_id=a,contact_user_id=b))
        db.commit(); ensure_private(db,u.id,target.id)
        return {'ok':True,'status':'accepted','chat_created':True}
    req=db.scalar(select(FriendRequest).where(FriendRequest.sender_id==u.id,FriendRequest.receiver_id==target.id))
    if req and req.status=='pending': return {'ok':True,'status':'pending'}
    if req: req.status='pending'; req.responded_at=None
    else: db.add(FriendRequest(sender_id=u.id,receiver_id=target.id))
    db.commit(); return {'ok':True,'status':'pending'}

@router.post('/request/respond')
def respond(data:RespondIn,db:Session=Depends(get_db),u=Depends(current_user)):
    req=db.get(FriendRequest,data.request_id)
    if not req or req.receiver_id!=u.id or req.status!='pending': raise HTTPException(404,'Запрос не найден')
    now=datetime.now(timezone.utc); req.status='accepted' if data.accept else 'rejected'; req.responded_at=now
    if data.accept:
        for a,b in ((req.sender_id,req.receiver_id),(req.receiver_id,req.sender_id)):
            if not db.scalar(select(Contact).where(Contact.owner_id==a,Contact.contact_user_id==b)): db.add(Contact(owner_id=a,contact_user_id=b))
    db.commit()
    chat=None
    if data.accept: chat=ensure_private(db,req.sender_id,req.receiver_id)
    return {'ok':True,'status':req.status,'chat_id':chat.id if chat else None}
