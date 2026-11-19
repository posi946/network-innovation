"""JWT authentication dependency (Day 3)."""
from __future__ import annotations

from typing import Any

from fastapi import Header, HTTPException

from ..core.config import settings


class FakeUser(dict):
    pass


def _decode_token(token: str) -> dict[str, Any]:
    try:
        from jose import jwt
        return jwt.decode(
            token,
            settings.supabase_jwt_secret or settings.secret_key,
            algorithms=["HS256"],
            audience="authenticated",
        )
    except ImportError:
        # Local development without python-jose: accept a dev token "dev:<user-id>".
        if token.startswith("dev:"):
            return {"sub": token[4:]}
        raise HTTPException(401, "Invalid authentication token")
    except Exception as exc:
        raise HTTPException(401, f"Invalid or expired token: {exc}")


def get_current_user(authorization: str | None = Header(default=None)) -> FakeUser:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(401, "Missing authentication token")
    payload = _decode_token(authorization.split(" ", 1)[1].strip())
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(401, "Token missing subject")
    return FakeUser(id=user_id, email=payload.get("email", ""), claims=payload)


def get_optional_user(authorization: str | None = Header(default=None)) -> FakeUser | None:
    try:
        return get_current_user(authorization)
    except HTTPException:
        return None
