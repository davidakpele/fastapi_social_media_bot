from datetime import datetime, timedelta
from fastapi import HTTPException, status
from jose import JWTError, jwt
from passlib.context import CryptContext
from typing import Optional, Dict, Any
from app.config import settings
import re

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Hash password
def hash_password(password: str) -> str:
    return pwd_context.hash(password)

# Verify password
def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def validate_email(email: str) -> bool:
    return re.match(r"[^@]+@[^@]+\.[^@]+", email) is not None

# Create JWT
def create_access_token(
    data: Dict[str, Any],
    role: Optional[Dict[str, bool]] = None,
    expires_delta: Optional[timedelta] = None
) -> str:
    """
    Create a JWT token with sub, name, role, iat, and exp.
    Default expiration: 30 days if expires_delta not provided.
    """
    to_encode = data.copy()

    if role:
        to_encode["role"] = role

    expire = datetime.utcnow() + (expires_delta or timedelta(days=30))
    to_encode["exp"] = expire
    to_encode["iat"] = datetime.utcnow()

    token = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return token

# Decode JWT
def decode_access_token(token: str):
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload
    except JWTError:
        return None


def auth_error(details: str):
    """Helper to build a consistent auth error response."""
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail={
            "error": "Access Denied",
            "status": "error",
            "title": "Authentication Error",
            "message": "Authorization Access",
            "details": details,
            "code": "generic_authentication_error",
        },
    )