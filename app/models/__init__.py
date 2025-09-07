# app/models/__init__.py
from .user import User
from .account import Account
# also import Post if you have it
from .post import Post  

__all__ = ["User", "Account", "Post"]
