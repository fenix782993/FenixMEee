from pathlib import Path

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy import select

from backend.api import auth, users, chats, messages, search, files, extras, social
from backend.core.config import settings
from backend.core.db import Base, engine, SessionLocal
from backend.core.security import token_user_id
from backend.models import User, chat_members
from backend.services.ws import manager

Base.metadata.create_all(engine)

def _db_migrate():
    """Small additive migration for existing SQLite/PostgreSQL installs.

    create_all() does not add columns to tables that already exist. Older
    Fenix databases may therefore be missing the email column even though
    the current User model has it. Add only missing columns; never drop data.
    """
    try:
        from sqlalchemy import inspect, text
        dialect = engine.dialect.name
        insp = inspect(engine)
        tables = set(insp.get_table_names())
        if "users" not in tables:
            return
        cols = {c["name"] for c in insp.get_columns("users")}
        with engine.begin() as conn:
            if dialect == "postgresql":
                if "role" not in cols:
                    conn.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS role VARCHAR(20) DEFAULT 'user'"))
                if "public_code" not in cols:
                    conn.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS public_code VARCHAR(4)"))
                if "email" not in cols:
                    conn.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS email VARCHAR(320)"))
            elif dialect == "sqlite":
                if "role" not in cols: conn.execute(text("ALTER TABLE users ADD COLUMN role VARCHAR(20) DEFAULT 'user'"))
                if "public_code" not in cols: conn.execute(text("ALTER TABLE users ADD COLUMN public_code VARCHAR(4)"))
                if "email" not in cols: conn.execute(text("ALTER TABLE users ADD COLUMN email VARCHAR(320)"))
    except Exception as exc:
        import logging
        logging.getLogger("fenix.db").exception("Database migration warning: %s", exc)

_db_migrate()

# Ensure the email column exists for databases created by older Fenix builds.

app = FastAPI(
    title=settings.app_name,
    version="12.0.0",
    description="Fenix Messenger API and web application",
)

@app.middleware("http")
async def app_headers(request, call_next):
    response = await call_next(request)
    if request.url.path.startswith("/api/"):
        response.headers["Cache-Control"] = "no-store"
        response.headers["Content-Type"] = response.headers.get("Content-Type", "application/json; charset=utf-8")
    elif request.url.path == "/" or request.url.path.endswith(".html") or request.url.path.endswith(".js") or request.url.path.endswith(".css"):
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    return response

origins = [x.strip() for x in settings.cors_origins.split(",") if x.strip()]
allow_all = not origins or origins == ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if allow_all else origins,
    allow_credentials=not allow_all,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api")
app.include_router(users.router, prefix="/api")
app.include_router(chats.router, prefix="/api")
app.include_router(messages.router, prefix="/api")
app.include_router(search.router, prefix="/api")
app.include_router(files.router, prefix="/api")
app.include_router(extras.router, prefix="/api")
app.include_router(social.router, prefix="/api")

BASE_DIR = Path(__file__).resolve().parent.parent
UPLOADS = Path(settings.upload_dir)
if not UPLOADS.is_absolute():
    UPLOADS = BASE_DIR / UPLOADS
UPLOADS.mkdir(parents=True, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=str(UPLOADS)), name="uploads")

FRONTEND_DIST = BASE_DIR / "frontend" / "dist"

@app.get("/api/health")
def health():
    return {
        "status": "ok",
        "service": "fenix-messenger",
        "version": "12.0.0",
        "frontend": "ready" if (FRONTEND_DIST / "index.html").exists() else "not_built",
    }

@app.get("/api/info")
def info():
    return {"name": "Fenix Messenger", "version": "12.0.0", "features": [
        "auth", "private_chats", "groups", "channels", "messages", "reactions", "pinning",
        "editing", "deleting", "search", "uploads", "websocket", "profile", "avatars", "favorites",
        "emoji", "stickers", "gifs", "drafts", "read_receipts", "blocking", "owner_codes", "group_admins",
        "settings", "calls", "themes", "mobile"
    ]}

@app.websocket("/ws/{chat_id}")
async def websocket(ws: WebSocket, chat_id: int):
    token = ws.query_params.get("token", "")
    uid = token_user_id(token)
    if not uid:
        await ws.close(code=1008, reason="Authentication required")
        return
    with SessionLocal() as db:
        member = db.scalar(
            select(chat_members.c.user_id).where(
                chat_members.c.chat_id == chat_id,
                chat_members.c.user_id == uid,
            )
        )
    if member is None:
        await ws.close(code=1008, reason="Not a chat member")
        return
    await manager.connect(chat_id, ws)
    try:
        while True:
            data = await ws.receive_json()
            event_type = data.get("type")
            if event_type in {"typing", "recording", "presence"}:
                await manager.broadcast(chat_id, {**data, "chat_id": chat_id, "user_id": uid})
    except WebSocketDisconnect:
        manager.disconnect(chat_id, ws)
    except Exception:
        manager.disconnect(chat_id, ws)

if FRONTEND_DIST.exists() and (FRONTEND_DIST / "index.html").exists():
    app.mount("/", StaticFiles(directory=str(FRONTEND_DIST), html=True), name="frontend")
