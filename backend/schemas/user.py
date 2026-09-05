from datetime import datetime
from pydantic import BaseModel
class UserOut(BaseModel):
    id: int
    username: str
    display_name: str
    avatar: str | None
    bio: str
    online: bool
    last_seen: datetime | None
    class Config: from_attributes = True
class ProfileUpdate(BaseModel):
    display_name: str | None = None
    bio: str | None = None
    avatar: str | None = None
