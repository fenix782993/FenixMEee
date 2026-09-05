from pydantic import BaseModel, Field
class PrivateChatIn(BaseModel):
    other_user_id: int
class GroupCreateIn(BaseModel):
    title: str = Field(min_length=1, max_length=120)
    description: str = Field(default="", max_length=500)
    member_ids: list[int] = Field(default_factory=list)
class ChatOut(BaseModel):
    id: int; kind: str; title: str; username: str; description: str; avatar: str | None
