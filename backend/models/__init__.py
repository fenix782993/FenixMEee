# Central model exports. Keep every model imported here so SQLAlchemy registers
# all tables before Base.metadata.create_all() runs in backend.main.
from .user import User
from .chat import Chat, chat_members
from .message import Message
from .reaction import Reaction
from .read import ReadState
from .favorite import Favorite
from .social import Block, Draft, GroupAdmin, CallSession
from .settings import UserSettings
from .email_verification import EmailVerification
from .phone_verification import PhoneVerification
from .contacts import Contact, FriendRequest

__all__ = [
    "User", "Chat", "chat_members", "Message", "Reaction", "ReadState",
    "Favorite", "Block", "Draft", "GroupAdmin", "CallSession",
    "UserSettings", "EmailVerification", "PhoneVerification",
    "Contact", "FriendRequest",
]
