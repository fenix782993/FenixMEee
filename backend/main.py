import os
from pathlib import Path
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import FastAPI, Depends, HTTPException, WebSocket, WebSocketDisconnect, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from sqlalchemy import (
    create_engine,
    Column,
    Integer,
    String,
    Text,
    Boolean,
    DateTime,
    ForeignKey,
    Table,
)
from sqlalchemy.orm import declarative_base, sessionmaker, Session, relationship

from jose import jwt, JWTError
from passlib.context import CryptContext
from pydantic import BaseModel


# ============================================================
# CONFIG
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent
BACKEND_DIR = BASE_DIR / "backend"
FRONTEND_DIR = BASE_DIR / "frontend"
FRONTEND_DIST = FRONTEND_DIR / "dist"
UPLOADS_DIR = BACKEND_DIR / "uploads"

UPLOADS_DIR.mkdir(parents=True, exist_ok=True)

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "sqlite:///./data.db"
)

# Render/PostgreSQL sometimes provides postgres://
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace(
        "postgres://",
        "postgresql://",
        1
    )

JWT_SECRET = os.getenv(
    "JWT_SECRET",
    "change-this-secret-in-production"
)

JWT_ALGORITHM = "HS256"
TOKEN_EXPIRE_HOURS = 168


# ============================================================
# DATABASE
# ============================================================

connect_args = {}

if DATABASE_URL.startswith("sqlite"):
    connect_args = {
        "check_same_thread": False
    }

engine = create_engine(
    DATABASE_URL,
    connect_args=connect_args,
    pool_pre_ping=True,
)

SessionLocal = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
)

Base = declarative_base()


# ============================================================
# MODELS
# ============================================================

chat_members = Table(
    "chat_members",
    Base.metadata,
    Column(
        "chat_id",
        Integer,
        ForeignKey("chats.id"),
        primary_key=True,
    ),
    Column(
        "user_id",
        Integer,
        ForeignKey("users.id"),
        primary_key=True,
    ),
)


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)

    username = Column(
        String(50),
        unique=True,
        nullable=False,
        index=True,
    )

    password_hash = Column(
        String(255),
        nullable=False,
    )

    display_name = Column(
        String(100),
        nullable=False,
    )

    avatar = Column(
        String(500),
        nullable=True,
    )

    bio = Column(
        Text,
        nullable=True,
    )

    online = Column(
        Boolean,
        default=False,
    )

    created_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
    )


class Chat(Base):
    __tablename__ = "chats"

    id = Column(
        Integer,
        primary_key=True,
        index=True,
    )

    title = Column(
        String(150),
        nullable=True,
    )

    kind = Column(
        String(30),
        default="private",
    )

    created_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
    )

    members = relationship(
        "User",
        secondary=chat_members,
        lazy="joined",
    )


class Message(Base):
    __tablename__ = "messages"

    id = Column(
        Integer,
        primary_key=True,
        index=True,
    )

    chat_id = Column(
        Integer,
        ForeignKey("chats.id"),
        nullable=False,
        index=True,
    )

    sender_id = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=False,
    )

    text = Column(
        Text,
        default="",
    )

    file_url = Column(
        String(1000),
        nullable=True,
    )

    reply_to_id = Column(
        Integer,
        nullable=True,
    )

    edited = Column(
        Boolean,
        default=False,
    )

    pinned = Column(
        Boolean,
        default=False,
    )

    created_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        index=True,
    )


Base.metadata.create_all(bind=engine)


# ============================================================
# APP
# ============================================================

app = FastAPI(
    title="Fenix Messenger API",
    version="2.0.0",
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================
# PASSWORD / JWT
# ============================================================

pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto",
)


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(
    password: str,
    password_hash: str,
) -> bool:
    return pwd_context.verify(
        password,
        password_hash,
    )


def create_token(user_id: int) -> str:
    expires = datetime.now(timezone.utc) + timedelta(
        hours=TOKEN_EXPIRE_HOURS
    )

    payload = {
        "sub": str(user_id),
        "exp": expires,
    }

    return jwt.encode(
        payload,
        JWT_SECRET,
        algorithm=JWT_ALGORITHM,
    )


def get_user_from_token(
    token: str,
    db: Session,
) -> User:

    try:
        payload = jwt.decode(
            token,
            JWT_SECRET,
            algorithms=[JWT_ALGORITHM],
        )

        user_id = payload.get("sub")

        if not user_id:
            raise HTTPException(
                status_code=401,
                detail="Invalid token",
            )

        user = db.get(
            User,
            int(user_id),
        )

        if not user:
            raise HTTPException(
                status_code=401,
                detail="User not found",
            )

        return user

    except JWTError:
        raise HTTPException(
            status_code=401,
            detail="Invalid token",
        )


def get_db():
    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()


def get_current_user(
    token: str,
    db: Session = Depends(get_db),
) -> User:

    return get_user_from_token(
        token,
        db,
    )


# ============================================================
# SCHEMAS
# ============================================================

class RegisterRequest(BaseModel):
    username: str
    password: str
    display_name: Optional[str] = None


class LoginRequest(BaseModel):
    username: str
    password: str


class MessageRequest(BaseModel):
    text: str
    reply_to_id: Optional[int] = None


class PrivateChatRequest(BaseModel):
    user_id: int


class GroupRequest(BaseModel):
    title: str


class EditMessageRequest(BaseModel):
    text: str


class ReactionRequest(BaseModel):
    reaction: str


# ============================================================
# SERIALIZERS
# ============================================================

def user_json(user: User):
    return {
        "id": user.id,
        "username": user.username,
        "display_name": user.display_name,
        "avatar": user.avatar,
        "bio": user.bio,
        "online": bool(user.online),
        "created_at": (
            user.created_at.isoformat()
            if user.created_at
            else None
        ),
    }


def message_json(message: Message):
    return {
        "id": message.id,
        "chat_id": message.chat_id,
        "sender_id": message.sender_id,
        "text": message.text,
        "file_url": message.file_url,
        "reply_to_id": message.reply_to_id,
        "edited": bool(message.edited),
        "pinned": bool(message.pinned),
        "created_at": (
            message.created_at.isoformat()
            if message.created_at
            else None
        ),
    }


def chat_json(chat: Chat, current_user_id: Optional[int] = None):

    members = [
        user_json(member)
        for member in chat.members
    ]

    title = chat.title

    if (
        chat.kind == "private"
        and current_user_id is not None
    ):
        other = next(
            (
                member
                for member in chat.members
                if member.id != current_user_id
            ),
            None,
        )

        if other:
            title = other.display_name

    return {
        "id": chat.id,
        "title": title,
        "kind": chat.kind,
        "members": members,
        "created_at": (
            chat.created_at.isoformat()
            if chat.created_at
            else None
        ),
    }


# ============================================================
# HEALTH
# ============================================================

@app.get("/api/health")
def health():
    return {
        "status": "ok",
        "service": "fenix-messenger",
        "version": "2.0.0",
    }


@app.get("/api")
def api_root():
    return {
        "name": "Fenix Messenger API",
        "status": "online",
    }


# ============================================================
# AUTH
# ============================================================

@app.post("/api/auth/register")
def register(
    data: RegisterRequest,
    db: Session = Depends(get_db),
):

    username = data.username.strip().lower()

    if len(username) < 3:
        raise HTTPException(
            status_code=400,
            detail="Username must contain at least 3 characters",
        )

    if len(data.password) < 6:
        raise HTTPException(
            status_code=400,
            detail="Password must contain at least 6 characters",
        )

    existing = (
        db.query(User)
        .filter(User.username == username)
        .first()
    )

    if existing:
        raise HTTPException(
            status_code=409,
            detail="Username already exists",
        )

    user = User(
        username=username,
        password_hash=hash_password(data.password),
        display_name=(
            data.display_name.strip()
            if data.display_name
            else username
        ),
        online=True,
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    token = create_token(user.id)

    return {
        "access_token": token,
        "token_type": "bearer",
        "user": user_json(user),
    }


@app.post("/api/auth/login")
def login(
    data: LoginRequest,
    db: Session = Depends(get_db),
):

    username = data.username.strip().lower()

    user = (
        db.query(User)
        .filter(User.username == username)
        .first()
    )

    if not user:
        raise HTTPException(
            status_code=401,
            detail="Invalid username or password",
        )

    if not verify_password(
        data.password,
        user.password_hash,
    ):
        raise HTTPException(
            status_code=401,
            detail="Invalid username or password",
        )

    user.online = True

    db.commit()

    token = create_token(user.id)

    return {
        "access_token": token,
        "token_type": "bearer",
        "user": user_json(user),
    }


@app.post("/api/auth/logout")
def logout(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):

    current_user.online = False
    db.commit()

    return {
        "success": True,
    }


# ============================================================
# USER
# ============================================================

@app.get("/api/me")
def me(
    current_user: User = Depends(get_current_user),
):
    return user_json(current_user)


@app.get("/api/users")
def users(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):

    result = (
        db.query(User)
        .filter(User.id != current_user.id)
        .order_by(User.online.desc(), User.username.asc())
        .all()
    )

    return [
        user_json(user)
        for user in result
    ]


@app.get("/api/users/{user_id}")
def get_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):

    user = db.get(User, user_id)

    if not user:
        raise HTTPException(
            status_code=404,
            detail="User not found",
        )

    return user_json(user)


# ============================================================
# PRIVATE CHAT
# ============================================================

@app.post("/api/chats/private")
def create_private_chat(
    data: PrivateChatRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):

    if data.user_id == current_user.id:
        raise HTTPException(
            status_code=400,
            detail="Cannot create chat with yourself",
        )

    other = db.get(
        User,
        data.user_id,
    )

    if not other:
        raise HTTPException(
            status_code=404,
            detail="User not found",
        )

    chats = (
        db.query(Chat)
        .filter(Chat.kind == "private")
        .all()
    )

    for chat in chats:

        ids = {
            member.id
            for member in chat.members
        }

        if ids == {
            current_user.id,
            other.id,
        }:
            return chat_json(
                chat,
                current_user.id,
            )

    chat = Chat(
        kind="private",
    )

    chat.members = [
        current_user,
        other,
    ]

    db.add(chat)
    db.commit()
    db.refresh(chat)

    return chat_json(
        chat,
        current_user.id,
    )


@app.post("/api/chats/group")
def create_group(
    data: GroupRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):

    title = data.title.strip()

    if not title:
        raise HTTPException(
            status_code=400,
            detail="Group title is required",
        )

    chat = Chat(
        title=title,
        kind="group",
    )

    chat.members = [
        current_user
    ]

    db.add(chat)
    db.commit()
    db.refresh(chat)

    return chat_json(
        chat,
        current_user.id,
    )


@app.get("/api/chats")
def get_chats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):

    chats = (
        db.query(Chat)
        .filter(
            Chat.members.any(
                User.id == current_user.id
            )
        )
        .order_by(
            Chat.created_at.desc()
        )
        .all()
    )

    return [
        chat_json(
            chat,
            current_user.id,
        )
        for chat in chats
    ]


# ============================================================
# MESSAGES
# ============================================================

def ensure_chat_member(
    chat_id: int,
    user_id: int,
    db: Session,
):

    chat = db.get(
        Chat,
        chat_id,
    )

    if not chat:
        raise HTTPException(
            status_code=404,
            detail="Chat not found",
        )

    member_ids = {
        member.id
        for member in chat.members
    }

    if user_id not in member_ids:
        raise HTTPException(
            status_code=403,
            detail="You are not a member of this chat",
        )

    return chat


@app.get("/api/chats/{chat_id}/messages")
def get_messages(
    chat_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):

    ensure_chat_member(
        chat_id,
        current_user.id,
        db,
    )

    messages = (
        db.query(Message)
        .filter(
            Message.chat_id == chat_id
        )
        .order_by(
            Message.created_at.asc()
        )
        .limit(500)
        .all()
    )

    return [
        message_json(message)
        for message in messages
    ]


@app.post("/api/chats/{chat_id}/messages")
def send_message(
    chat_id: int,
    data: MessageRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):

    ensure_chat_member(
        chat_id,
        current_user.id,
        db,
    )

    text = data.text.strip()

    if not text:
        raise HTTPException(
            status_code=400,
            detail="Message cannot be empty",
        )

    message = Message(
        chat_id=chat_id,
        sender_id=current_user.id,
        text=text,
        reply_to_id=data.reply_to_id,
    )

    db.add(message)
    db.commit()
    db.refresh(message)

    return message_json(message)


@app.patch("/api/messages/{message_id}")
def edit_message(
    message_id: int,
    data: EditMessageRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):

    message = db.get(
        Message,
        message_id,
    )

    if not message:
        raise HTTPException(
            status_code=404,
            detail="Message not found",
        )

    if message.sender_id != current_user.id:
        raise HTTPException(
            status_code=403,
            detail="You can edit only your messages",
        )

    text = data.text.strip()

    if not text:
        raise HTTPException(
            status_code=400,
            detail="Message cannot be empty",
        )

    message.text = text
    message.edited = True

    db.commit()
    db.refresh(message)

    await_broadcast(
        message.chat_id,
        {
            "type": "message_edit",
            "message": message_json(message),
        },
    )

    return message_json(message)


@app.delete("/api/messages/{message_id}")
def delete_message(
    message_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):

    message = db.get(
        Message,
        message_id,
    )

    if not message:
        raise HTTPException(
            status_code=404,
            detail="Message not found",
        )

    if message.sender_id != current_user.id:
        raise HTTPException(
            status_code=403,
            detail="You can delete only your messages",
        )

    chat_id = message.chat_id

    db.delete(message)
    db.commit()

    await_broadcast(
        chat_id,
        {
            "type": "message_delete",
            "message_id": message_id,
        },
    )

    return {
        "success": True,
        "message_id": message_id,
    }


@app.post("/api/messages/{message_id}/pin")
def pin_message(
    message_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):

    message = db.get(
        Message,
        message_id,
    )

    if not message:
        raise HTTPException(
            status_code=404,
            detail="Message not found",
        )

    ensure_chat_member(
        message.chat_id,
        current_user.id,
        db,
    )

    message.pinned = not message.pinned

    db.commit()
    db.refresh(message)

    return message_json(message)


@app.post("/api/messages/{message_id}/reaction")
def reaction(
    message_id: int,
    data: ReactionRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):

    message = db.get(
        Message,
        message_id,
    )

    if not message:
        raise HTTPException(
            status_code=404,
            detail="Message not found",
        )

    ensure_chat_member(
        message.chat_id,
        current_user.id,
        db,
    )

    return {
        "success": True,
        "message_id": message_id,
        "reaction": data.reaction,
        "user_id": current_user.id,
    }


# ============================================================
# FILE UPLOAD
# ============================================================

@app.post("/api/upload")
async def upload_file(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
):

    original_name = file.filename or "file"

    safe_name = "".join(
        char
        for char in original_name
        if char.isalnum()
        or char in "._-"
    )

    if not safe_name:
        safe_name = "file"

    timestamp = int(
        datetime.now(timezone.utc).timestamp()
    )

    filename = (
        f"{current_user.id}_"
        f"{timestamp}_"
        f"{safe_name}"
    )

    destination = UPLOADS_DIR / filename

    content = await file.read()

    # 25 MB
    if len(content) > 25 * 1024 * 1024:
        raise HTTPException(
            status_code=413,
            detail="File is too large. Maximum 25 MB.",
        )

    destination.write_bytes(content)

    return {
        "success": True,
        "filename": filename,
        "url": f"/uploads/{filename}",
        "original_name": original_name,
    }


if UPLOADS_DIR.exists():
    app.mount(
        "/uploads",
        StaticFiles(
            directory=str(UPLOADS_DIR)
        ),
        name="uploads",
    )


# ============================================================
# WEBSOCKET
# ============================================================

connections = {}


class ConnectionManager:

    def __init__(self):
        self.connections = {}

    async def connect(
        self,
        chat_id: int,
        websocket: WebSocket,
    ):
        await websocket.accept()

        self.connections.setdefault(
            chat_id,
            [],
        ).append(websocket)

    def disconnect(
        self,
        chat_id: int,
        websocket: WebSocket,
    ):

        if chat_id not in self.connections:
            return

        if websocket in self.connections[chat_id]:
            self.connections[chat_id].remove(
                websocket
            )

        if not self.connections[chat_id]:
            del self.connections[chat_id]

    async def broadcast(
        self,
        chat_id: int,
        data,
    ):

        sockets = list(
            self.connections.get(
                chat_id,
                [],
            )
        )

        dead = []

        for websocket in sockets:

            try:
                await websocket.send_json(
                    data
                )
            except Exception:
                dead.append(websocket)

        for websocket in dead:
            self.disconnect(
                chat_id,
                websocket,
            )


manager = ConnectionManager()


def await_broadcast(
    chat_id: int,
    data,
):
    """
    HTTP endpoints не могут напрямую await-ить
    здесь. Это место оставлено для совместимости.
    Основной realtime работает через WebSocket.
    """
    return None


@app.websocket("/ws/{chat_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    chat_id: int,
):

    token = websocket.query_params.get(
        "token"
    )

    if not token:
        await websocket.close(
            code=1008
        )
        return

    db = SessionLocal()

    try:

        try:
            user = get_user_from_token(
                token,
                db,
            )
        except HTTPException:
            await websocket.close(
                code=1008
            )
            return

        chat = db.get(
            Chat,
            chat_id,
        )

        if not chat:
            await websocket.close(
                code=1008
            )
            return

        member_ids = {
            member.id
            for member in chat.members
        }

        if user.id not in member_ids:
            await websocket.close(
                code=1008
            )
            return

        user.online = True
        db.commit()

        await manager.connect(
            chat_id,
            websocket,
        )

        await manager.broadcast(
            chat_id,
            {
                "type": "presence",
                "user_id": user.id,
                "online": True,
            },
        )

        while True:

            data = await websocket.receive_json()

            event_type = data.get(
                "type"
            )

            if event_type == "typing":

                await manager.broadcast(
                    chat_id,
                    {
                        "type": "typing",
                        "user_id": user.id,
                        "typing": bool(
                            data.get(
                                "typing",
                                True,
                            )
                        ),
                    },
                )

            elif event_type == "message":

                text = str(
                    data.get(
                        "text",
                        "",
                    )
                ).strip()

                if not text:
                    continue

                message = Message(
                    chat_id=chat_id,
                    sender_id=user.id,
                    text=text,
                    reply_to_id=data.get(
                        "reply_to_id"
                    ),
                )

                db.add(message)
                db.commit()
                db.refresh(message)

                await manager.broadcast(
                    chat_id,
                    {
                        "type": "message",
                        "message": message_json(
                            message
                        ),
                    },
                )

            elif event_type == "ping":

                await websocket.send_json(
                    {
                        "type": "pong"
                    }
                )

    except WebSocketDisconnect:

        manager.disconnect(
            chat_id,
            websocket,
        )

        try:
            user = get_user_from_token(
                token,
                db,
            )

            user.online = False
            db.commit()

            await manager.broadcast(
                chat_id,
                {
                    "type": "presence",
                    "user_id": user.id,
                    "online": False,
                },
            )

        except Exception:
            pass

    except Exception:

        manager.disconnect(
            chat_id,
            websocket,
        )

    finally:
        db.close()


# ============================================================
# FRONTEND
# ============================================================

def frontend_available():
    return (
        FRONTEND_DIST.exists()
        and (
            FRONTEND_DIST / "index.html"
        ).exists()
    )


if frontend_available():

    assets_dir = FRONTEND_DIST / "assets"

    if assets_dir.exists():

        app.mount(
            "/assets",
            StaticFiles(
                directory=str(assets_dir)
            ),
            name="frontend-assets",
        )


    @app.get(
        "/",
        include_in_schema=False,
    )
    async def frontend_root():

        return FileResponse(
            FRONTEND_DIST / "index.html"
        )


    @app.get(
        "/{path:path}",
        include_in_schema=False,
    )
    async def frontend_fallback(
        path: str,
    ):

        # Никогда не перехватываем API
        if path.startswith("api/"):
            return JSONResponse(
                status_code=404,
                content={
                    "detail": "API endpoint not found"
                },
            )

        # Никогда не перехватываем WebSocket
        if path.startswith("ws/"):
            return JSONResponse(
                status_code=404,
                content={
                    "detail": "WebSocket endpoint not found"
                },
            )

        requested = (
            FRONTEND_DIST / path
        )

        # Например favicon.svg
        if requested.is_file():
            return FileResponse(
                requested
            )

        # React Router
        return FileResponse(
            FRONTEND_DIST / "index.html"
        )


else:

    @app.get(
        "/",
        include_in_schema=False,
    )
    async def frontend_missing():

        return JSONResponse(
            status_code=503,
            content={
                "service": "Fenix Messenger",
                "status": "backend_online",
                "frontend": "not_built",
                "message": (
                    "FastAPI работает, "
                    "но frontend/dist/index.html "
                    "не найден."
                ),
            },
        )


# ============================================================
# STARTUP
# ============================================================

@app.on_event("startup")
async def startup():

    print("=" * 60)
    print("FENIX MESSENGER")
    print("=" * 60)

    print(
        f"Base directory: {BASE_DIR}"
    )

    print(
        f"Frontend dist: {FRONTEND_DIST}"
    )

    print(
        f"Frontend available: "
        f"{frontend_available()}"
    )

    print(
        f"Database: "
        f"{DATABASE_URL.split('@')[-1]}"
    )

    print("=" * 60)
