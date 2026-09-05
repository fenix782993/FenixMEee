import os, json, uuid, asyncio
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Optional
from fastapi import FastAPI, Depends, HTTPException, UploadFile, File, WebSocket, WebSocketDisconnect, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from sqlalchemy import create_engine, String, Integer, Boolean, Text, DateTime, ForeignKey, func, or_, and_
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship, sessionmaker, Session
from jose import jwt, JWTError
from passlib.context import CryptContext

BASE=Path(__file__).resolve().parent
UPLOADS=Path(os.getenv('UPLOAD_DIR', BASE/'uploads')); UPLOADS.mkdir(parents=True,exist_ok=True)
DATABASE_URL=os.getenv('DATABASE_URL','sqlite:///./data.db')
if DATABASE_URL.startswith('postgres://'): DATABASE_URL=DATABASE_URL.replace('postgres://','postgresql://',1)
engine=create_engine(DATABASE_URL,connect_args={'check_same_thread':False} if DATABASE_URL.startswith('sqlite') else {})
SessionLocal=sessionmaker(bind=engine,autoflush=False,autocommit=False)
JWT_SECRET=os.getenv('JWT_SECRET','dev-only-change-me'); ALG='HS256'; pwd=CryptContext(schemes=['bcrypt'],deprecated='auto')

class Base(DeclarativeBase): pass
class User(Base):
    __tablename__='users'; id:Mapped[int]=mapped_column(primary_key=True); username:Mapped[str]=mapped_column(String(32),unique=True,index=True); password_hash:Mapped[str]=mapped_column(String(255)); display_name:Mapped[str]=mapped_column(String(80)); bio:Mapped[str]=mapped_column(Text,default=''); avatar:Mapped[str]=mapped_column(String(500),default=''); online:Mapped[bool]=mapped_column(Boolean,default=False); last_seen:Mapped[datetime]=mapped_column(DateTime,default=lambda:datetime.now(timezone.utc))
class Chat(Base):
    __tablename__='chats'; id:Mapped[int]=mapped_column(primary_key=True); title:Mapped[str]=mapped_column(String(120)); kind:Mapped[str]=mapped_column(String(20),default='private'); created_at:Mapped[datetime]=mapped_column(DateTime,default=lambda:datetime.now(timezone.utc)); creator_id:Mapped[int]=mapped_column(ForeignKey('users.id')); members=relationship('ChatMember',back_populates='chat',cascade='all, delete-orphan'); messages=relationship('Message',back_populates='chat',cascade='all, delete-orphan')
class ChatMember(Base):
    __tablename__='chat_members'; id:Mapped[int]=mapped_column(primary_key=True); chat_id:Mapped[int]=mapped_column(ForeignKey('chats.id'),index=True); user_id:Mapped[int]=mapped_column(ForeignKey('users.id'),index=True); role:Mapped[str]=mapped_column(String(20),default='member'); muted:Mapped[bool]=mapped_column(Boolean,default=False); last_read_id:Mapped[int]=mapped_column(Integer,default=0); chat=relationship('Chat',back_populates='members'); user=relationship('User')
class Message(Base):
    __tablename__='messages'; id:Mapped[int]=mapped_column(primary_key=True); chat_id:Mapped[int]=mapped_column(ForeignKey('chats.id'),index=True); sender_id:Mapped[int]=mapped_column(ForeignKey('users.id')); text:Mapped[str]=mapped_column(Text,default=''); attachment:Mapped[str]=mapped_column(String(500),default=''); attachment_name:Mapped[str]=mapped_column(String(255),default=''); reply_to:Mapped[int]=mapped_column(Integer,default=0); edited:Mapped[bool]=mapped_column(Boolean,default=False); deleted:Mapped[bool]=mapped_column(Boolean,default=False); pinned:Mapped[bool]=mapped_column(Boolean,default=False); reactions:Mapped[str]=mapped_column(Text,default='{}'); created_at:Mapped[datetime]=mapped_column(DateTime,default=lambda:datetime.now(timezone.utc)); chat=relationship('Chat',back_populates='messages')
Base.metadata.create_all(engine)

def db():
    s=SessionLocal();
    try: yield s
    finally: s.close()
def token_for(u): return jwt.encode({'sub':str(u.id),'exp':datetime.now(timezone.utc)+timedelta(days=30)},JWT_SECRET,algorithm=ALG)
def auth(token:str,s:Session):
    try: uid=int(jwt.decode(token,JWT_SECRET,algorithms=[ALG])['sub'])
    except (JWTError,ValueError,KeyError): raise HTTPException(401,'Invalid token')
    u=s.get(User,uid)
    if not u: raise HTTPException(401,'User not found')
    return u
def user_json(u): return {'id':u.id,'username':u.username,'display_name':u.display_name,'bio':u.bio,'avatar':u.avatar,'online':u.online,'last_seen':u.last_seen.isoformat() if u.last_seen else None}
def msg_json(m,s):
    u=s.get(User,m.sender_id); r=json.loads(m.reactions or '{}'); return {'id':m.id,'chat_id':m.chat_id,'sender_id':m.sender_id,'sender':user_json(u) if u else None,'text':m.text,'attachment':m.attachment,'attachment_name':m.attachment_name,'reply_to':m.reply_to,'edited':m.edited,'deleted':m.deleted,'pinned':m.pinned,'reactions':r,'created_at':m.created_at.isoformat()}
def chat_json(c,s,me):
    members=[s.get(User,x.user_id) for x in c.members]; others=[u for u in members if u and u.id!=me.id]; title=c.title or (others[0].display_name if others else 'Чат'); last=s.query(Message).filter(Message.chat_id==c.id).order_by(Message.id.desc()).first(); unread=s.query(Message).filter(Message.chat_id==c.id,Message.id>max([x.last_read_id for x in c.members if x.user_id==me.id] or [0]),Message.sender_id!=me.id).count(); return {'id':c.id,'title':title,'kind':c.kind,'created_at':c.created_at.isoformat(),'members':[user_json(u) for u in members if u],'last_message':msg_json(last,s) if last else None,'unread':unread}

app=FastAPI(title='Fenix Messenger API',version='2.0.0')
origins=os.getenv('CORS_ORIGINS','*').split(','); app.add_middleware(CORSMiddleware,allow_origins=origins,allow_credentials=True,allow_methods=['*'],allow_headers=['*'])
class AuthIn(BaseModel): username:str=Field(min_length=3,max_length=32); password:str=Field(min_length=6,max_length=128); display_name:str=''
class ChatIn(BaseModel): kind:str='private'; user_id:Optional[int]=None; title:str=''; member_ids:list[int]=[]
class MessageIn(BaseModel): text:str=''; attachment:str=''; attachment_name:str=''; reply_to:int=0
class EditIn(BaseModel): text:str
class ReactionIn(BaseModel): emoji:str=Field(min_length=1,max_length=8)
class ProfileIn(BaseModel): display_name:str=Field(min_length=1,max_length=80); bio:str=''; avatar:str=''

@app.get('/api/health')
def health(): return {'ok':True,'service':'fenix-messenger'}
@app.post('/api/auth/register')
def register(x:AuthIn,s:Session=Depends(db)):
    username=x.username.lower().strip();
    if s.query(User).filter_by(username=username).first(): raise HTTPException(409,'Username already exists')
    u=User(username=username,password_hash=pwd.hash(x.password),display_name=x.display_name.strip() or username); s.add(u); s.commit(); s.refresh(u); return {'token':token_for(u),'user':user_json(u)}
@app.post('/api/auth/login')
def login(x:AuthIn,s:Session=Depends(db)):
    u=s.query(User).filter_by(username=x.username.lower().strip()).first()
    if not u or not pwd.verify(x.password,u.password_hash): raise HTTPException(401,'Wrong username or password')
    u.online=True;u.last_seen=datetime.now(timezone.utc);s.commit();return {'token':token_for(u),'user':user_json(u)}
@app.get('/api/me')
def me(token:str=Query(...),s:Session=Depends(db)): return user_json(auth(token,s))
@app.patch('/api/me')
def edit_profile(x:ProfileIn,token:str,s:Session=Depends(db)):
    u=auth(token,s);u.display_name=x.display_name;u.bio=x.bio;u.avatar=x.avatar;s.commit();return user_json(u)
@app.get('/api/users')
def users(q:str='',token:str=Query(...),s:Session=Depends(db)):
    u=auth(token,s); query=s.query(User).filter(User.id!=u.id);
    if q: query=query.filter(or_(User.username.ilike(f'%{q}%'),User.display_name.ilike(f'%{q}%')))
    return [user_json(x) for x in query.order_by(User.online.desc(),User.display_name).limit(50).all()]
@app.post('/api/chats')
def create_chat(x:ChatIn,token:str,s:Session=Depends(db)):
    me=auth(token,s); ids={me.id,*x.member_ids};
    if x.kind=='private':
        if not x.user_id: raise HTTPException(400,'user_id required')
        ids.add(x.user_id); other=x.user_id; existing=s.query(Chat).filter(Chat.kind=='private').all()
        for c in existing:
            mids={m.user_id for m in c.members}
            if mids=={me.id,other}: return chat_json(c,s,me)
    c=Chat(title=x.title.strip() or ('Группа' if x.kind=='group' else ''),kind=x.kind,creator_id=me.id);s.add(c);s.flush()
    for uid in ids:
        if s.get(User,uid): s.add(ChatMember(chat_id=c.id,user_id=uid,role='owner' if uid==me.id else 'member'))
    s.commit();s.refresh(c);return chat_json(c,s,me)
@app.get('/api/chats')
def chats(token:str=Query(...),s:Session=Depends(db)):
    me=auth(token,s); cs=s.query(Chat).join(ChatMember).filter(ChatMember.user_id==me.id).order_by(Chat.created_at.desc()).all(); return [chat_json(c,s,me) for c in cs]
def member(chat_id,uid,s): return s.query(ChatMember).filter_by(chat_id=chat_id,user_id=uid).first()
@app.get('/api/chats/{cid}/messages')
def get_messages(cid:int,limit:int=50,before:int=0,token:str=Query(...),s:Session=Depends(db)):
    u=auth(token,s);
    if not member(cid,u.id,s): raise HTTPException(403,'Not a member')
    q=s.query(Message).filter(Message.chat_id==cid).order_by(Message.id.desc());
    if before:q=q.filter(Message.id<before)
    return [msg_json(m,s) for m in reversed(q.limit(min(limit,100)).all())]

connections:dict[int,set[WebSocket]]={}
async def push(cid,payload):
    dead=[]
    for w in list(connections.get(cid,set())):
        try: await w.send_json(payload)
        except: dead.append(w)
    for w in dead: connections.get(cid,set()).discard(w)
@app.post('/api/chats/{cid}/messages')
def send_message(cid:int,x:MessageIn,token:str,s:Session=Depends(db)):
    u=auth(token,s);
    if not member(cid,u.id,s): raise HTTPException(403,'Not a member')
    if not x.text.strip() and not x.attachment: raise HTTPException(400,'Empty message')
    m=Message(chat_id=cid,sender_id=u.id,text=x.text.strip(),attachment=x.attachment,attachment_name=x.attachment_name,reply_to=x.reply_to);s.add(m);s.commit();s.refresh(m); data=msg_json(m,s); asyncio.create_task(push(cid,{'type':'message','message':data})); return data
@app.patch('/api/messages/{mid}')
def edit_message(mid:int,x:EditIn,token:str,s:Session=Depends(db)):
    u=auth(token,s);m=s.get(Message,mid)
    if not m or m.sender_id!=u.id:raise HTTPException(404,'Message not found')
    m.text=x.text.strip();m.edited=True;s.commit();data=msg_json(m,s);asyncio.create_task(push(m.chat_id,{'type':'message_edit','message':data}));return data
@app.delete('/api/messages/{mid}')
def delete_message(mid:int,token:str,s:Session=Depends(db)):
    u=auth(token,s);m=s.get(Message,mid)
    if not m or m.sender_id!=u.id:raise HTTPException(404,'Message not found')
    m.deleted=True;m.text='';m.attachment='';s.commit();data=msg_json(m,s);asyncio.create_task(push(m.chat_id,{'type':'message_delete','message':data}));return data
@app.post('/api/messages/{mid}/reaction')
def reaction(mid:int,x:ReactionIn,token:str,s:Session=Depends(db)):
    u=auth(token,s);m=s.get(Message,mid)
    if not m or not member(m.chat_id,u.id,s):raise HTTPException(404,'Message not found')
    r=json.loads(m.reactions or '{}'); arr=r.setdefault(x.emoji,[]);
    if u.id in arr:arr.remove(u.id)
    else:arr.append(u.id)
    if not arr: r.pop(x.emoji,None)
    m.reactions=json.dumps(r);s.commit();data=msg_json(m,s);asyncio.create_task(push(m.chat_id,{'type':'reaction','message':data}));return data
@app.post('/api/messages/{mid}/pin')
def pin(mid:int,token:str,s:Session=Depends(db)):
    u=auth(token,s);m=s.get(Message,mid)
    if not m or not member(m.chat_id,u.id,s):raise HTTPException(404,'Message not found')
    m.pinned=not m.pinned;s.commit();data=msg_json(m,s);asyncio.create_task(push(m.chat_id,{'type':'pin','message':data}));return data
@app.get('/api/chats/{cid}/search')
def search_messages(cid:int,q:str,token:str=Query(...),s:Session=Depends(db)):
    u=auth(token,s);
    if not member(cid,u.id,s):raise HTTPException(403,'Not a member')
    return [msg_json(m,s) for m in s.query(Message).filter(Message.chat_id==cid,Message.text.ilike(f'%{q}%')).order_by(Message.id.desc()).limit(50).all()]
@app.post('/api/chats/{cid}/read')
def mark_read(cid:int,message_id:int,token:str,s:Session=Depends(db)):
    u=auth(token,s);cm=member(cid,u.id,s)
    if not cm:raise HTTPException(403,'Not a member')
    cm.last_read_id=max(cm.last_read_id,message_id);s.commit();asyncio.create_task(push(cid,{'type':'read','user_id':u.id,'message_id':message_id}));return {'ok':True}
@app.post('/api/upload')
def upload(file:UploadFile=File(...),token:str=Query(...),s:Session=Depends(db)):
    auth(token,s); ext=Path(file.filename or '').suffix[:12]; name=f'{uuid.uuid4().hex}{ext}';dest=UPLOADS/name
    with dest.open('wb') as out: out.write(file.file.read())
    return {'url':f'/uploads/{name}','name':file.filename or name}
@app.websocket('/ws/{cid}')
async def websocket(ws:WebSocket,cid:int,token:str):
    s=SessionLocal()
    try:
        u=auth(token,s);c=s.get(Chat,cid)
        if not c or not member(cid,u.id,s): await ws.close(code=1008);return
        await ws.accept();connections.setdefault(cid,set()).add(ws);u.online=True;u.last_seen=datetime.now(timezone.utc);s.commit();await push(cid,{'type':'presence','user_id':u.id,'online':True})
        while True:
            d=await ws.receive_json();typ=d.get('type')
            if typ=='typing':await push(cid,{'type':'typing','user_id':u.id,'typing':bool(d.get('typing'))})
            elif typ=='read':await push(cid,{'type':'read','user_id':u.id,'message_id':d.get('message_id')})
            elif typ=='ping':await ws.send_json({'type':'pong'})
    except WebSocketDisconnect:pass
    except Exception:pass
    finally:
        connections.get(cid,set()).discard(ws);u.online=False;u.last_seen=datetime.now(timezone.utc);s.commit();await push(cid,{'type':'presence','user_id':u.id,'online':False});s.close()
app.mount('/uploads',StaticFiles(directory=UPLOADS),name='uploads')
DIST=BASE.parent/'frontend'/'dist'
if DIST.exists():
    app.mount('/assets',StaticFiles(directory=DIST/'assets'),name='assets')
    @app.get('/{path:path}')
    def frontend(path:str):
        f=DIST/path;return FileResponse(f if f.exists() and f.is_file() else DIST/'index.html')
