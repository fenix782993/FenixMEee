from datetime import datetime, timezone
import json, secrets
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select, or_, delete
from sqlalchemy.orm import Session
from backend.api.deps import current_user
from backend.core.db import get_db
from backend.models import User, Chat, Block, Draft, ReadState, GroupAdmin, CallSession, UserSettings, chat_members
from backend.services.chat_service import members

router=APIRouter(prefix='/social',tags=['social'])

class TextIn(BaseModel): text:str=Field(default='',max_length=10000)
class UserIdIn(BaseModel): user_id:int
class SettingsIn(BaseModel):
    theme:str|None=None; language:str|None=None; notifications:bool|None=None; sounds:bool|None=None; dnd:bool|None=None; privacy:str|None=None
class ChannelIn(BaseModel):
    title:str=Field(min_length=1,max_length=120); username:str=Field(min_length=5,max_length=64,pattern=r'^[A-Za-z0-9_]+$'); description:str=''; is_public:bool=True
class AdminIn(BaseModel): user_id:int; can_manage:bool=True; can_delete:bool=True; can_ban:bool=True; can_pin:bool=True
class CallIn(BaseModel): callee_id:int; kind:str='audio'; chat_id:int|None=None
class SignalIn(BaseModel): value:str=Field(max_length=200000)

def out_user(u):
    return {'id':u.id,'public_code':u.public_code,'username':u.username,'display_name':u.display_name,'avatar':u.avatar,'bio':u.bio,'online':u.online,'role':u.role,'last_seen':u.last_seen,'created_at':u.created_at}

@router.get('/people')
def people(q:str='',db:Session=Depends(get_db),u=Depends(current_user)):
    q=q.strip().lstrip('@')
    if len(q)<2:return []
    blocked={x.blocked_user_id for x in db.scalars(select(Block).where(Block.user_id==u.id)).all()}
    stmt=select(User).where(User.id!=u.id)
    if q.isdigit() and len(q) in (3,4): stmt=stmt.where(User.public_code==q)
    else: stmt=stmt.where(or_(User.username.ilike(f'%{q}%'),User.display_name.ilike(f'%{q}%')))
    return [out_user(x) for x in db.scalars(stmt.limit(50)).all() if x.id not in blocked]

@router.post('/block')
def block(data:UserIdIn,db:Session=Depends(get_db),u=Depends(current_user)):
    if data.user_id==u.id or not db.get(User,data.user_id): raise HTTPException(404,'Пользователь не найден')
    if not db.scalar(select(Block).where(Block.user_id==u.id,Block.blocked_user_id==data.user_id)): db.add(Block(user_id=u.id,blocked_user_id=data.user_id)); db.commit()
    return {'ok':True}
@router.delete('/block/{user_id}')
def unblock(user_id:int,db:Session=Depends(get_db),u=Depends(current_user)):
    db.execute(delete(Block).where(Block.user_id==u.id,Block.blocked_user_id==user_id)); db.commit(); return {'ok':True}
@router.get('/blocked')
def blocked(db:Session=Depends(get_db),u=Depends(current_user)):
    return [out_user(db.get(User,x.blocked_user_id)) for x in db.scalars(select(Block).where(Block.user_id==u.id)).all() if db.get(User,x.blocked_user_id)]

@router.get('/drafts/{chat_id}')
def draft(chat_id:int,db:Session=Depends(get_db),u=Depends(current_user)):
    d=db.scalar(select(Draft).where(Draft.user_id==u.id,Draft.chat_id==chat_id)); return {'text':d.text if d else ''}
@router.put('/drafts/{chat_id}')
def save_draft(chat_id:int,data:TextIn,db:Session=Depends(get_db),u=Depends(current_user)):
    if u.id not in members(db,chat_id): raise HTTPException(403,'Нет доступа')
    d=db.scalar(select(Draft).where(Draft.user_id==u.id,Draft.chat_id==chat_id))
    if not d: d=Draft(user_id=u.id,chat_id=chat_id,text=data.text); db.add(d)
    else: d.text=data.text
    db.commit(); return {'ok':True}

@router.post('/read/{chat_id}/{message_id}')
def read(chat_id:int,message_id:int,db:Session=Depends(get_db),u=Depends(current_user)):
    if u.id not in members(db,chat_id): raise HTTPException(403,'Нет доступа')
    r=db.scalar(select(ReadState).where(ReadState.user_id==u.id,ReadState.chat_id==chat_id))
    if not r: r=ReadState(user_id=u.id,chat_id=chat_id,last_message_id=message_id); db.add(r)
    else: r.last_message_id=max(r.last_message_id,message_id)
    db.commit(); return {'ok':True,'last_message_id':r.last_message_id}

@router.get('/settings')
def settings_get(db:Session=Depends(get_db),u=Depends(current_user)):
    s=db.scalar(select(UserSettings).where(UserSettings.user_id==u.id))
    if not s: s=UserSettings(user_id=u.id); db.add(s); db.commit(); db.refresh(s)
    return {'theme':s.theme,'language':s.language,'notifications':s.notifications,'sounds':s.sounds,'dnd':s.dnd,'privacy':s.privacy}
@router.patch('/settings')
def settings_patch(data:SettingsIn,db:Session=Depends(get_db),u=Depends(current_user)):
    s=db.scalar(select(UserSettings).where(UserSettings.user_id==u.id))
    if not s: s=UserSettings(user_id=u.id); db.add(s)
    for k,v in data.model_dump(exclude_none=True).items(): setattr(s,k,v)
    db.commit(); return settings_get(db,u)

@router.post('/channels')
def create_channel(data:ChannelIn,db:Session=Depends(get_db),u=Depends(current_user)):
    if db.scalar(select(Chat).where(Chat.username==data.username.lower())): raise HTTPException(409,'Username канала занят')
    c=Chat(kind='channel',title=data.title,username=data.username.lower(),description=data.description,is_public=data.is_public,avatar=None)
    db.add(c); db.flush(); db.execute(chat_members.insert().values(chat_id=c.id,user_id=u.id)); db.add(GroupAdmin(chat_id=c.id,user_id=u.id)); db.commit(); db.refresh(c)
    return {'id':c.id,'kind':c.kind,'title':c.title,'username':c.username,'description':c.description,'avatar':c.avatar,'is_public':c.is_public}
@router.post('/groups/{chat_id}/admins')
def add_admin(chat_id:int,data:AdminIn,db:Session=Depends(get_db),u=Depends(current_user)):
    c=db.get(Chat,chat_id)
    if not c or c.kind!='group': raise HTTPException(404,'Группа не найдена')
    if u.role!='owner' and not db.scalar(select(GroupAdmin).where(GroupAdmin.chat_id==chat_id,GroupAdmin.user_id==u.id,GroupAdmin.can_manage==True)): raise HTTPException(403,'Нет прав')
    if data.user_id not in members(db,chat_id): raise HTTPException(400,'Пользователь не в группе')
    a=db.scalar(select(GroupAdmin).where(GroupAdmin.chat_id==chat_id,GroupAdmin.user_id==data.user_id))
    if not a: a=GroupAdmin(chat_id=chat_id,user_id=data.user_id); db.add(a)
    for k in ('can_manage','can_delete','can_ban','can_pin'): setattr(a,k,getattr(data,k))
    db.commit(); return {'ok':True}
@router.get('/groups/{chat_id}/admins')
def admins(chat_id:int,db:Session=Depends(get_db),u=Depends(current_user)):
    if u.id not in members(db,chat_id): raise HTTPException(403,'Нет доступа')
    return [{'user':out_user(db.get(User,a.user_id)),'can_manage':a.can_manage,'can_delete':a.can_delete,'can_ban':a.can_ban,'can_pin':a.can_pin} for a in db.scalars(select(GroupAdmin).where(GroupAdmin.chat_id==chat_id)).all()]

@router.post('/calls')
def call(data:CallIn,db:Session=Depends(get_db),u=Depends(current_user)):
    if not db.get(User,data.callee_id) or data.callee_id==u.id: raise HTTPException(404,'Пользователь не найден')
    c=CallSession(caller_id=u.id,callee_id=data.callee_id,chat_id=data.chat_id,kind=data.kind if data.kind in ('audio','video') else 'audio',status='ringing'); db.add(c); db.commit(); db.refresh(c)
    return {'id':c.id,'status':c.status,'kind':c.kind,'caller_id':u.id,'callee_id':data.callee_id}
@router.patch('/calls/{call_id}/offer')
def offer(call_id:int,data:SignalIn,db:Session=Depends(get_db),u=Depends(current_user)):
    c=db.get(CallSession,call_id)
    if not c or u.id not in (c.caller_id,c.callee_id): raise HTTPException(404,'Звонок не найден')
    c.offer=data.value; db.commit(); return {'ok':True}
@router.patch('/calls/{call_id}/answer')
def answer(call_id:int,data:SignalIn,db:Session=Depends(get_db),u=Depends(current_user)):
    c=db.get(CallSession,call_id)
    if not c or u.id not in (c.caller_id,c.callee_id): raise HTTPException(404,'Звонок не найден')
    c.answer=data.value; c.status='active'; db.commit(); return {'ok':True}
@router.post('/calls/{call_id}/end')
def end_call(call_id:int,db:Session=Depends(get_db),u=Depends(current_user)):
    c=db.get(CallSession,call_id)
    if not c or u.id not in (c.caller_id,c.callee_id): raise HTTPException(404,'Звонок не найден')
    c.status='ended'; c.ended_at=datetime.now(timezone.utc); db.commit(); return {'ok':True}
