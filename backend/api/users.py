from fastapi import APIRouter, Depends
from sqlalchemy import select, or_
from sqlalchemy.orm import Session
from backend.api.deps import current_user
from backend.core.db import get_db
from backend.models import User
from backend.schemas.user import UserOut, ProfileUpdate

router = APIRouter(prefix="/users", tags=["users"])

@router.get("", response_model=list[UserOut])
def users(q: str = "", limit: int = 50, db: Session = Depends(get_db), u=Depends(current_user)):
    limit = max(1, min(limit, 100))
    stmt = select(User).where(User.id != u.id)
    if q:
        stmt = stmt.where(or_(User.username.ilike(f"%{q}%"), User.display_name.ilike(f"%{q}%")))
    return db.scalars(stmt.limit(limit)).all()

@router.get("/me", response_model=UserOut)
def me(u=Depends(current_user)):
    return u

@router.patch("/me", response_model=UserOut)
def update(data: ProfileUpdate, u=Depends(current_user), db: Session = Depends(get_db)):
    for key, value in data.model_dump(exclude_none=True).items():
        setattr(u, key, value)
    db.commit()
    db.refresh(u)
    return u
