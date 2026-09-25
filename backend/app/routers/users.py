from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status
from bson import ObjectId
from ..database import db
from ..dependencies import require_roles, serialize
from ..schemas import UserCreate
from ..security import hash_password

router = APIRouter(prefix="/users", tags=["Users"])


@router.get("")
async def list_users(_: dict = Depends(require_roles("admin", "manager"))):
    return {"items": [serialize(item) async for item in db.users.find({}, {"password_hash": 0}).sort("full_name", 1)]}


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_user(payload: UserCreate, _: dict = Depends(require_roles("admin"))):
    if await db.users.find_one({"email": payload.email.lower()}):
        raise HTTPException(status_code=409, detail="Email is already registered")
    user = payload.model_dump()
    user["email"] = user["email"].lower()
    user["role"] = user["role"].value
    user["password_hash"] = hash_password(user.pop("password"))
    user["is_active"] = True
    user["created_at"] = datetime.now(timezone.utc)
    result = await db.users.insert_one(user)
    return {"user": serialize(await db.users.find_one({"_id": result.inserted_id}, {"password_hash": 0}))}
