from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, delete
from sqlalchemy.orm import Session
from backend.api.deps import current_user
from backend.core.db import get_db
from backend.models import User, Message, Favorite
from backend.schemas.user import UserOut, CodeIssueIn
import random

router=APIRouter(prefix='/extras',tags=['extras'])
EMOJIS='😀 😃 😄 😁 😆 😅 😂 🤣 😊 😇 🙂 🙃 😉 😌 😍 🥰 😘 😗 😙 😚 😋 😛 😝 😜 🤪 🤨 🧐 🤓 😎 🤩 🥳 😏 😒 😞 😔 😟 😕 🙁 ☹️ 😣 😖 😫 😩 🥺 😢 😭 😤 😠 😡 🤬 🤯 😳 🥵 🥶 😱 😨 😰 😥 😓 🤗 🤔 🫡 🤭 🤫 🤥 😶 🫠 😐 😑 😬 🙄 😯 😦 😧 😮 😲 🥱 😴 🤤 😪 😵 🤐 🤑 🤠'.split()
STICKERS=[{'id':f'fox{i}','emoji':e,'name':f'Fenix Sticker {i}'} for i,e in enumerate('🦊 🐺 🐻 🐼 🐨 🐯 🦁 🐸 🐵 🐱 🐶 🐰 🐹 🐭 🐷 🐮 🐣 🐧 🦄 🐝 🦋 🐙 🦑 🐬 🐳 🦈 🐲 👻 🤖 👾 💀 👽 🎃'.split(),1)]

@router.get('/emoji')
def emoji(u=Depends(current_user)): return {'items':EMOJIS}
@router.get('/stickers')
def stickers(u=Depends(current_user)): return {'items':STICKERS}
@router.get('/gifs')
def gifs(q:str='',u=Depends(current_user)):
    q=(q or 'funny').strip()[:50]
    return {'provider':'local','items':[{'id':f'gif{i}','title':f'{q} GIF {i}','url':f'https://media.giphy.com/media/ICOgUNjpvO0PC/giphy.gif'} for i in range(1,9)]}

@router.post('/favorites/{message_id}')
def toggle_favorite(message_id:int, db:Session=Depends(get_db),u=Depends(current_user)):
    m=db.get(Message,message_id)
    if not m: raise HTTPException(404,'Сообщение не найдено')
    r=db.scalar(select(Favorite).where(Favorite.user_id==u.id,Favorite.message_id==message_id))
    if r: db.delete(r); state=False
    else: db.add(Favorite(user_id=u.id,message_id=message_id)); state=True
    db.commit(); return {'favorite':state}

@router.get('/favorites')
def favorites(db:Session=Depends(get_db),u=Depends(current_user)):
    rows=db.scalars(select(Favorite).where(Favorite.user_id==u.id).order_by(Favorite.id.desc()).limit(200)).all()
    out=[]
    for r in rows:
        m=db.get(Message,r.message_id)
        if m: out.append({'id':r.id,'message_id':m.id,'chat_id':m.chat_id,'sender_id':m.sender_id,'text':m.text,'media_url':m.media_url,'created_at':m.created_at})
    return out

@router.post('/owner/issue-code')
def issue_code(data:CodeIssueIn,db:Session=Depends(get_db),u=Depends(current_user)):
    if u.role!='owner': raise HTTPException(403,'Только владелец')
    if len(data.code) not in (3,4) or not data.code.isdigit(): raise HTTPException(422,'Код должен содержать 3 или 4 цифры')
    target=db.get(User,data.user_id)
    if not target: raise HTTPException(404,'Пользователь не найден')
    taken=db.scalar(select(User).where(User.public_code==data.code,User.id!=target.id))
    if taken: raise HTTPException(409,'Этот код уже занят')
    target.public_code=data.code; db.commit(); db.refresh(target)
    return user_dict(target)

def user_dict(u): return UserOut.model_validate(u,from_attributes=True)
