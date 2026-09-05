from datetime import datetime
from pydantic import BaseModel
class UserOut(BaseModel):
    id: int
    public_code: str | None = None
    username: str
    display_name: str
    avatar: str | None
    bio: str
    online: bool
    role: str = 'user'
    last_seen: datetime | None
    class Config: from_attributes = True
class ProfileUpdate(BaseModel):
    display_name: str | None = None
    bio: str | None = None
    avatar: str | None = None
class CodeIssueIn(BaseModel):
    user_id: int
    code: str
