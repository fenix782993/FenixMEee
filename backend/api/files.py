import os, uuid
from pathlib import Path
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from backend.api.deps import current_user
from backend.core.config import settings

router = APIRouter(prefix="/files", tags=["files"])
UPLOAD_DIR = Path(settings.upload_dir)
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
MAX_SIZE = 25 * 1024 * 1024

@router.post("/upload")
async def upload(file: UploadFile = File(...), u=Depends(current_user)):
    if not file.filename:
        raise HTTPException(400, "Filename is required")
    ext = os.path.splitext(file.filename)[1][:16]
    name = f"{uuid.uuid4().hex}{ext}"
    path = UPLOAD_DIR / name
    size = 0
    with path.open("wb") as out:
        while chunk := await file.read(1024 * 1024):
            size += len(chunk)
            if size > MAX_SIZE:
                path.unlink(missing_ok=True)
                raise HTTPException(413, "File is too large (25 MB max)")
            out.write(chunk)
    return {"url": f"/uploads/{name}", "name": file.filename, "content_type": file.content_type, "size": size}

@router.post('/avatar')
async def avatar_upload(file: UploadFile = File(...), u=Depends(current_user)):
    if not file.filename or not (file.content_type or '').startswith('image/'):
        raise HTTPException(400, 'Можно загрузить только изображение')
    ext = os.path.splitext(file.filename)[1].lower()[:8] or '.jpg'
    name=f'avatar_{u.id}_{uuid.uuid4().hex}{ext}'
    path=UPLOAD_DIR/name; size=0
    with path.open('wb') as out:
        while chunk:=await file.read(512*1024):
            size+=len(chunk)
            if size>8*1024*1024:
                path.unlink(missing_ok=True); raise HTTPException(413,'Аватар максимум 8 МБ')
            out.write(chunk)
    u.avatar=f'/uploads/{name}'
    from backend.core.db import SessionLocal
    with SessionLocal() as db:
        user=db.get(type(u),u.id); user.avatar=f'/uploads/{name}'; db.commit()
    return {'url':f'/uploads/{name}'}
