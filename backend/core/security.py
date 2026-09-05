from datetime import datetime, timedelta, timezone
from jose import JWTError, jwt
from pwdlib import PasswordHash
from .config import settings

password_hash = PasswordHash.recommended()

def hash_password(value: str) -> str:
    return password_hash.hash(value)

def verify_password(value: str, hashed: str) -> bool:
    try:
        return password_hash.verify(value, hashed)
    except Exception:
        return False

def create_token(user_id: int) -> str:
    now = datetime.now(timezone.utc)
    payload = {"sub": str(user_id), "iat": int(now.timestamp()), "exp": int((now + timedelta(minutes=settings.access_token_minutes)).timestamp()), "typ": "access"}
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)

def token_user_id(token: str) -> int | None:
    if not token:
        return None
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
        return int(payload["sub"])
    except (JWTError, KeyError, ValueError, TypeError):
        return None
