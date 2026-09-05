from fastapi import Depends, Header, HTTPException
from sqlalchemy.orm import Session
from backend.core.db import get_db
from backend.core.security import token_user_id
from backend.models import User

def current_user(authorization: str = Header(default=""), db: Session = Depends(get_db)):
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Требуется авторизация")
    uid = token_user_id(authorization[7:].strip())
    user = db.get(User, uid) if uid else None
    if user is None:
        raise HTTPException(status_code=401, detail="Сессия недействительна. Войдите снова")
    return user
