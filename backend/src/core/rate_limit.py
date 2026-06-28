from jose import JWTError, jwt
from slowapi import Limiter
from slowapi.util import get_remote_address

from src.core.config import settings


def _get_user_or_ip(request) -> str:
    """Rate limit key: authenticated user email, or client IP as fallback."""
    auth = request.headers.get("Authorization", "")
    if auth.startswith("Bearer "):
        try:
            payload = jwt.decode(auth[7:], settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
            email = payload.get("sub")
            if email:
                return email
        except JWTError:
            pass
    return get_remote_address(request)


# For multi-instance deployments, swap storage_uri to a Redis URL, e.g.:
#   Limiter(key_func=_get_user_or_ip, storage_uri="redis://redis:6379")
limiter = Limiter(key_func=_get_user_or_ip)
