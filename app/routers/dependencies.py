from app.utils.security import decode_access_token
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer
from typing import Optional


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


# No Authorization header at all
class CustomOAuth2PasswordBearer(OAuth2PasswordBearer):
    async def __call__(self, request: Request) -> str:
        try:
            return await super().__call__(request)
        except HTTPException:
            raise auth_error("No authentication token provided in request.")


# use the custom OAuth2 scheme
oauth2_scheme = CustomOAuth2PasswordBearer(tokenUrl="token")


def get_current_user(token: str = Depends(oauth2_scheme)):
    """
    FastAPI dependency to get the current user from a JWT token.
    Raises custom 401 if token is invalid or expired.
    """
    try:
        payload = decode_access_token(token)
        user_id: Optional[str] = payload.get("sub")
        if user_id is None:
            raise auth_error("Invalid authentication token: missing subject (sub).")
        return int(user_id)
    except Exception:
        raise auth_error("Invalid or expired authentication token.")
