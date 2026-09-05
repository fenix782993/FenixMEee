from datetime import datetime
from pydantic import BaseModel, Field
class MessageCreate(BaseModel):
    text: str = Field(default="", max_length=4000)
    reply_to_id: int | None = None
    media_url: str | None = None
    media_type: str | None = None
class MessageUpdate(BaseModel):
    text: str = Field(min_length=1, max_length=4000)
class ReactionIn(BaseModel):
    emoji: str = Field(min_length=1, max_length=16)
class MessageOut(BaseModel):
    id: int; chat_id: int; sender_id: int; text: str; media_url: str | None; media_type: str | None
    reply_to_id: int | None; edited: bool; deleted: bool; pinned: bool; created_at: datetime
