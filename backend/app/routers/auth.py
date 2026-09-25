from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status
from bson import ObjectId
from ..database import db
from ..dependencies import get_current_user, serialize
from ..schemas import LoginRequest, UserCreate
from ..security import create_access_token, hash_password, verify_password

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register(payload: UserCreate):
    if await db.users.find_one({"email": payload.email.lower()}):
        raise HTTPException(status_code=409, detail="Email is already registered")
    user = payload.model_dump()
    user["email"] = user["email"].lower()
    user["role"] = "requester"  # public registration cannot create privileged accounts
    user["password_hash"] = hash_password(user.pop("password"))
    user["is_active"] = True
    user["created_at"] = datetime.now(timezone.utc)
    result = await db.users.insert_one(user)
    return {"user": serialize(await db.users.find_one({"_id": result.inserted_id}))}


@router.post("/login")
async def login(payload: LoginRequest):
    user = await db.users.find_one({"email": payload.email.lower()})
    if not user or not verify_password(payload.password, user["password_hash"]):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect email or password")
    if not user.get("is_active", True):
        raise HTTPException(status_code=403, detail="Account is inactive")
    return {"access_token": create_access_token(str(user["_id"]), user["role"]), "token_type": "bearer", "user": serialize(user)}


@router.get("/me")
async def me(user: dict = Depends(get_current_user)):
    return {"user": user}
