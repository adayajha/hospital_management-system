from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status
from ..database import db
from ..dependencies import require_roles, serialize
from ..schemas import DepartmentCreate

router = APIRouter(prefix="/departments", tags=["Departments"])


@router.get("")
async def list_departments():
    return {"items": [serialize(item) async for item in db.departments.find().sort("name", 1)]}


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_department(payload: DepartmentCreate, _: dict = Depends(require_roles("admin"))):
    if await db.departments.find_one({"code": payload.code.upper()}):
        raise HTTPException(status_code=409, detail="Department code already exists")
    department = {**payload.model_dump(), "code": payload.code.upper(), "created_at": datetime.now(timezone.utc)}
    result = await db.departments.insert_one(department)
    return {"department": serialize(await db.departments.find_one({"_id": result.inserted_id}))}
