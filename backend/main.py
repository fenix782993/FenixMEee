import os, uuid, json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Optional
from fastapi import FastAPI, Depends, HTTPException, WebSocket, WebSocketDisconnect, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from jose import jwt, JWTError
from passlib.context import CryptContext
from sqlalchemy import create_engine, Column, Integer, String, Boolean, DateTime, ForeignKey, Text, Table, or_, and_
from sqlalchemy.orm import declarative_base, sessionmaker, Session, relationship

BASE = Path(__file__).resolve().parent
DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///./data.db')
if DATABASE_URL.startswith('postgres://'): DATABASE_URL = DATABASE_URL.replace('postgres://','postgresql://',1)
engine = create_engine(DATABASE_URL, connect_args={'check_same_thread': False} if DATABASE_URL.startswith('sqlite') else {})
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)
Base = declarative_base()
pwd = CryptContext(schemes=['bcrypt'], deprecated='auto')
SECRET = os.getenv('JWT_SECRET','dev-secret-change-me')
ALG = 'HS256'
UPLOADS = BASE / 'uploads'; UPLOADS.mkdir(exist_ok=True)

members = Table('chat_members', Base.metadata,
    Column('chat_id', ForeignKey('chats.id'), primary_key=True),
    Column('user_id', ForeignKey('users.id'), primary_key=True))

class User(Base):
    __tablename__='users'
    id=Column(Integer,primary_key=True); username=Column(String(64),unique=True,index=True,nullable=False)
    password_hash=Column(String(255),nullable=False); display_name=Column(String(120),nullable=False)
    avatar=Column(String(500)); bio=Column(String(500),default=''); online=Column(Boolean,default=False)
    created_at=Column(DateTime,default=lambda:datetime.now(timezone.utc))
class Chat(Base):
    __tablename__='chats'
    id=Column(Integer,primary_key=True); title=Column(String(160)); kind=Column(String(20),default='private')
    created_at=Column(DateTime,default=lambda:datetime.now(timezone.utc)); pinned=Column(Boolean,default=False)
    members=relationship('User',secondary=members)
class Message(Base):
    __tablename__='messages'
    id=Column(Integer,primary_key=True); chat_id=Column(Integer,ForeignKey('chats.id'),index=True)
    sender_id=Column(Integer,ForeignKey('users.id')); text=Column(Text,default=''); attachment=Column(String(500))
    reply_to=Column(Integer,ForeignKey('messages.id')); edited=Column(Boolean,default=False); deleted=Column(Boolean,default=False)
    created_at=Column(DateTime,default=lambda:datetime.now(timezone.utc)); reactions=Column(Text,default='{}')

Base.metadata.create_all(engine)
app=FastAPI(title='Fenix Messenger API',version='1.0.0')
app.add_middleware(CORSMiddleware,allow_origins=['*'],allow_credentials=True,allow_methods=['*'],allow_headers=['*'])
connections={}

def db():
    s=SessionLocal()
    try: yield s
    finally: s.close()
def token_for(u): return jwt.encode({'sub':str(u.id),'exp':datetime.now(timezone.utc)+timedelta(days=30)},SECRET,algorithm=ALG)
def current(token:str, s:Session):
    try: uid=int(jwt.decode(token,SECRET,algorithms=[ALG])['sub'])
    except (JWTError,ValueError,KeyError): raise HTTPException(401,'Invalid token')
    u=s.get(User,uid)
    if not u: raise HTTPException(401,'User not found')
    return u
def auth(s=Depends(db), authorization:Optional[str]=None):
    # FastAPI header dependency is handled manually by route helper.
    raise HTTPException(401,'Use bearer token')
def get_user(s, bearer):
    if not bearer or not bearer.startswith('Bearer '): raise HTTPException(401,'Authorization required')
    return current(bearer[7:],s)

class AuthIn(BaseModel): username:str; password:str; display_name:Optional[str]=None
class ProfileIn(BaseModel): display_name:str; bio:str=''; avatar:Optional[str]=None
class ChatIn(BaseModel): user_id:Optional[int]=None; title:Optional[str]=None; kind:str='private'; member_ids:list[int]=[]
class MsgIn(BaseModel): text:str=''; reply_to:Optional[int]=None; attachment:Optional[str]=None
class EditIn(BaseModel): text:str
class ReactionIn(BaseModel): emoji:str

@app.get('/api/health')
def health(): return {'ok':True,'service':'fenix-messenger'}
@app.post('/api/auth/register')
def register(x:AuthIn,s:Session=Depends(db)):
    if len(x.username)<3 or len(x.password)<6: raise HTTPException(400,'Username/password too short')
    if s.query(User).filter_by(username=x.username.lower()).first(): raise HTTPException(409,'Username already exists')
    u=User(username=x.username.lower(),display_name=x.display_name or x.username,password_hash=pwd.hash(x.password)); s.add(u); s.commit(); s.refresh(u)
    return {'token':token_for(u),'user':user_json(u)}
@app.post('/api/auth/login')
def login(x:AuthIn,s:Session=Depends(db)):
    u=s.query(User).filter_by(username=x.username.lower()).first()
    if not u or not pwd.verify(x.password,u.password_hash): raise HTTPException(401,'Invalid credentials')
    u.online=True; s.commit(); return {'token':token_for(u),'user':user_json(u)}
@app.get('/api/me')
def me(s:Session=Depends(db), authorization:Optional[str]=None): return user_json(get_user(s,authorization))

def user_json(u): return {'id':u.id,'username':u.username,'display_name':u.display_name,'avatar':u.avatar,'bio':u.bio,'online':u.online}
def chat_json(c,me_id,s):
    other=next((u for u in c.members if u.id!=me_id),None) if c.kind=='private' else None
    last=s.query(Message).filter_by(chat_id=c.id,deleted=False).order_by(Message.id.desc()).first()
    return {'id':c.id,'kind':c.kind,'title':c.title or (other.display_name if other else 'Группа'),'members':[user_json(u) for u in c.members], 'last_message':msg_json(last) if last else None}
def msg_json(m):
    if not m:return None
    return {'id':m.id,'chat_id':m.chat_id,'sender_id':m.sender_id,'text':'' if m.deleted else m.text,'attachment':m.attachment,'reply_to':m.reply_to,'edited':m.edited,'deleted':m.deleted,'created_at':m.created_at.isoformat(),'reactions':json.loads(m.reactions or '{}')}

@app.get('/api/users')
def users(s:Session=Depends(db),authorization:Optional[str]=None,q:str=''):
    u=get_user(s,authorization); query=s.query(User).filter(User.id!=u.id)
    if q: query=query.filter(or_(User.username.ilike(f'%{q}%'),User.display_name.ilike(f'%{q}%')))
    return [user_json(x) for x in query.order_by(User.display_name).limit(50)]
@app.put('/api/me')
def profile(x:ProfileIn,s:Session=Depends(db),authorization:Optional[str]=None):
    u=get_user(s,authorization); u.display_name=x.display_name;u.bio=x.bio;u.avatar=x.avatar;s.commit();return user_json(u)
@app.post('/api/chats')
def create_chat(x:ChatIn,s:Session=Depends(db),authorization:Optional[str]=None):
    u=get_user(s,authorization); ids=set(x.member_ids);ids.add(u.id)
    if x.kind=='private':
        if not x.user_id: raise HTTPException(400,'user_id required')
        ids={u.id,x.user_id}
        for c in s.query(Chat).filter_by(kind='private').all():
            if {m.id for m in c.members}==ids:return chat_json(c,u.id,s)
    c=Chat(kind=x.kind,title=x.title or 'Новая группа'); c.members=[s.get(User,i) for i in ids if s.get(User,i)];s.add(c);s.commit();s.refresh(c);return chat_json(c,u.id,s)
@app.get('/api/chats')
def chats(s:Session=Depends(db),authorization:Optional[str]=None):
    u=get_user(s,authorization); return [chat_json(c,u.id,s) for c in s.query(Chat).join(members).filter(members.c.user_id==u.id).order_by(Chat.id.desc()).all()]
@app.get('/api/chats/{cid}/messages')
def messages(cid:int,s:Session=Depends(db),authorization:Optional[str]=None,limit:int=100):
    u=get_user(s,authorization); c=s.get(Chat,cid)
    if not c or u not in c.members: raise HTTPException(403,'Forbidden')
    return [msg_json(m) for m in s.query(Message).filter_by(chat_id=cid).order_by(Message.id.desc()).limit(min(limit,200)).all()][::-1]
@app.post('/api/chats/{cid}/messages')
def send(cid:int,x:MsgIn,s:Session=Depends(db),authorization:Optional[str]=None):
    u=get_user(s,authorization);c=s.get(Chat,cid)
    if not c or u not in c.members:raise HTTPException(403,'Forbidden')
    m=Message(chat_id=cid,sender_id=u.id,text=x.text,reply_to=x.reply_to,attachment=x.attachment);s.add(m);s.commit();s.refresh(m); payload=msg_json(m); broadcast(cid,{'type':'message','message':payload});return payload
@app.patch('/api/messages/{mid}')
def edit(mid:int,x:EditIn,s:Session=Depends(db),authorization:Optional[str]=None):
    u=get_user(s,authorization);m=s.get(Message,mid)
    if not m or m.sender_id!=u.id:raise HTTPException(403,'Forbidden')
    m.text=x.text;m.edited=True;s.commit();p=msg_json(m);broadcast(m.chat_id,{'type':'message_edit','message':p});return p
@app.delete('/api/messages/{mid}')
def delete(mid:int,s:Session=Depends(db),authorization:Optional[str]=None):
    u=get_user(s,authorization);m=s.get(Message,mid)
    if not m or m.sender_id!=u.id:raise HTTPException(403,'Forbidden')
    m.deleted=True;m.text='';s.commit();p=msg_json(m);broadcast(m.chat_id,{'type':'message_delete','message':p});return p
@app.post('/api/messages/{mid}/reaction')
def reaction(mid:int,x:ReactionIn,s:Session=Depends(db),authorization:Optional[str]=None):
    u=get_user(s,authorization);m=s.get(Message,mid)
    if not m:raise HTTPException(404,'Message not found')
    r=json.loads(m.reactions or '{}');r.setdefault(x.emoji,[])
    if u.id in r[x.emoji]:r[x.emoji].remove(u.id)
    else:r[x.emoji].append(u.id)
    m.reactions=json.dumps(r);s.commit();p=msg_json(m);broadcast(m.chat_id,{'type':'reaction','message':p});return p
@app.post('/api/upload')
def upload(file:UploadFile=File(...)):
    ext=Path(file.filename or '').suffix[:10];name=f'{uuid.uuid4().hex}{ext}';dest=UPLOADS/name
    with dest.open('wb') as f:f.write(file.file.read())
    return {'url':f'/uploads/{name}','name':file.filename}
@app.websocket('/ws/{cid}')
async def ws(websocket:WebSocket,cid:int,token:str):
    s=SessionLocal()
    try:
        u=current(token,s);c=s.get(Chat,cid)
        if not c or u not in c.members: await websocket.close(code=1008);return
        await websocket.accept();connections.setdefault(cid,set()).add(websocket)
        while True:
            data=await websocket.receive_json()
            if data.get('type')=='typing': await broadcast_async(cid,{'type':'typing','user_id':u.id,'typing':bool(data.get('typing'))})
            elif data.get('type')=='read': await broadcast_async(cid,{'type':'read','user_id':u.id,'message_id':data.get('message_id')})
    except WebSocketDisconnect: pass
    finally:
        connections.get(cid,set()).discard(websocket);s.close()
def broadcast(cid,payload):
    import asyncio
    for w in list(connections.get(cid,set())):
        try: asyncio.create_task(w.send_json(payload))
        except Exception: pass
async def broadcast_async(cid,payload):
    for w in list(connections.get(cid,set())):
        try: await w.send_json(payload)
        except Exception: pass

app.mount('/uploads',StaticFiles(directory=UPLOADS),name='uploads')
DIST=BASE.parent/'frontend'/'dist'
if DIST.exists():
    app.mount('/assets',StaticFiles(directory=DIST/'assets'),name='assets')
    @app.get('/{path:path}')
    def frontend(path:str):
        f=DIST/path
        return FileResponse(f if f.exists() and f.is_file() else DIST/'index.html')
