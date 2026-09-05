from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, or_
from sqlalchemy.orm import Session
from backend.api.deps import current_user
from backend.core.db import get_db
from backend.models import User
from backend.schemas.user import UserOut, ProfileUpdate, CodeIssueIn

router = APIRouter(prefix='/users', tags=['users'])

def user_dict(u):
    return UserOut.model_validate(u, from_attributes=True)

@router.get('', response_model=list[UserOut])
def users(q: str = '', limit: int = 50, db: Session = Depends(get_db), u=Depends(current_user)):
    limit = max(1, min(limit, 100)); q=q.strip()
    stmt = select(User).where(User.id != u.id)
    if q:
        if q.isdigit() and len(q) in (3,4):
            stmt = stmt.where(User.public_code == q)
        else:
            stmt = stmt.where(or_(User.username.ilike(f'%{q}%'), User.display_name.ilike(f'%{q}%')))
    return list(db.scalars(stmt.limit(limit)).all())

@router.get('/me', response_model=UserOut)
def me(u=Depends(current_user)): return u

@router.patch('/me', response_model=UserOut)
def update(data: ProfileUpdate, u=Depends(current_user), db: Session = Depends(get_db)):
    values=data.model_dump(exclude_none=True)
    if 'display_name' in values and not values['display_name'].strip(): raise HTTPException(422,'Имя не может быть пустым')
    for key,value in values.items(): setattr(u,key,value)
    db.commit(); db.refresh(u); return u

@router.get('/by/{username}', response_model=UserOut)
def by_username(username: str, db: Session = Depends(get_db), u=Depends(current_user)):
    target=db.scalar(select(User).where(User.username==username.lower().lstrip('@')))
    if not target or target.id==u.id: raise HTTPException(404,'Пользователь не найден')
    return target
