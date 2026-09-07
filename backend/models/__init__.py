
from .contacts import Contact, FriendRequest, Block

# Re-export User when available.
try:
    from .user import User
except Exception:
    try:
        from .users import User
    except Exception:
        User = None

__all__ = ["Contact", "FriendRequest", "Block", "User"]
