from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from bson import ObjectId
from .database import db
from .security import decode_access_token

bearer = HTTPBearer()


def serialize(document: dict | None) -> dict | None:
    if document is None:
        return None
    result = dict(document)
    result["id"] = str(result.pop("_id"))
    return result


async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(bearer)) -> dict:
    try:
        payload = decode_access_token(credentials.credentials)
        user_id = payload["sub"]
        user = await db.users.find_one({"_id": ObjectId(user_id)})
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid authentication credentials") from exc
    if not user or not user.get("is_active", True):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User is unavailable")
    return serialize(user)


def require_roles(*roles: str):
    async def check(user: dict = Depends(get_current_user)) -> dict:
        if user["role"] not in roles:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")
        return user
    return check
