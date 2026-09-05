from fastapi import Depends, Header, HTTPException
from sqlalchemy.orm import Session
from backend.core.db import get_db
from backend.core.security import token_user_id
from backend.models import User

def current_user(authorization: str = Header(""), db: Session = Depends(get_db)):
    if not authorization.startswith("Bearer "): raise HTTPException(401,"Authorization required")
    uid=token_user_id(authorization[7:])
    user=db.get(User, uid) if uid else None
    if not user: raise HTTPException(401,"Invalid token")
    return user
