"""Central model registry.

Every SQLAlchemy model is imported exactly once from its defining module.
This prevents duplicate Table definitions in a shared MetaData instance.
"""
from .user import User
from .chat import Chat, chat_members
from .message import Message
from .reaction import Reaction
from .read import ReadState
from .favorite import Favorite
from .social import Block, Draft, GroupAdmin, CallSession
from .settings import UserSettings

__all__ = [
    "User", "Chat", "chat_members", "Message", "Reaction", "ReadState",
    "Favorite", "Block", "Draft", "GroupAdmin", "CallSession", "UserSettings",
]
