from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.api.deps import current_user
from backend.core.db import get_db
from backend.core.security import create_token, hash_password, verify_password
from backend.models import User
from backend.schemas.auth import RegisterIn, LoginIn, TokenOut

router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/register", response_model=TokenOut, status_code=201)
def register(data: RegisterIn, db: Session = Depends(get_db)):
    username = data.username.strip().lower()
    display_name = data.display_name.strip()
    if db.scalar(select(User).where(User.username == username)):
        raise HTTPException(409, "Пользователь с таким логином уже существует")
    user = User(username=username, display_name=display_name, password_hash=hash_password(data.password), online=True)
    db.add(user)
    db.commit()
    db.refresh(user)
    return TokenOut(access_token=create_token(user.id))

@router.post("/login", response_model=TokenOut)
def login(data: LoginIn, db: Session = Depends(get_db)):
    username = data.username.strip().lower()
    user = db.scalar(select(User).where(User.username == username))
    if user is None or not verify_password(data.password, user.password_hash):
        raise HTTPException(401, "Неверный логин или пароль")
    user.online = True
    db.commit()
    return TokenOut(access_token=create_token(user.id))

@router.get("/me")
def auth_me(u=Depends(current_user)):
    return u

@router.post("/logout")
def logout(u=Depends(current_user), db: Session = Depends(get_db)):
    u.online = False
    db.commit()
    return {"ok": True}
