from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.api.deps import current_user
from backend.core.db import get_db
from backend.core.security import create_token, hash_password, verify_password
from backend.models import User
from backend.schemas.auth import RegisterIn, LoginIn, TokenOut

router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/register", response_model=TokenOut)
def register(data: RegisterIn, db: Session = Depends(get_db)):
    if db.scalar(select(User).where(User.username == data.username)):
        raise HTTPException(409, "Username already exists")
    user = User(username=data.username, display_name=data.display_name, password_hash=hash_password(data.password), online=True)
    db.add(user)
    db.commit()
    db.refresh(user)
    return TokenOut(access_token=create_token(user.id))

@router.post("/login", response_model=TokenOut)
def login(data: LoginIn, db: Session = Depends(get_db)):
    user = db.scalar(select(User).where(User.username == data.username))
    if not user or not verify_password(data.password, user.password_hash):
        raise HTTPException(401, "Invalid credentials")
    user.online = True
    db.commit()
    return TokenOut(access_token=create_token(user.id))

@router.post("/logout")
def logout(u=Depends(current_user), db: Session = Depends(get_db)):
    u.online = False
    db.commit()
    return {"ok": True}
