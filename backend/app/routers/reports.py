from fastapi import APIRouter, Depends
from ..database import db
from ..dependencies import require_roles

router = APIRouter(prefix="/reports", tags=["Reports"])


@router.get("/summary")
async def summary(_: dict = Depends(require_roles("admin", "manager", "agent"))):
    pipeline = [{"$group": {"_id": "$status", "count": {"$sum": 1}}}]
    status_counts = {row["_id"]: row["count"] async for row in db.tickets.aggregate(pipeline)}
    priority_pipeline = [{"$group": {"_id": "$priority", "count": {"$sum": 1}}}]
    priorities = {row["_id"]: row["count"] async for row in db.tickets.aggregate(priority_pipeline)}
    return {"total": await db.tickets.count_documents({}), "by_status": status_counts, "by_priority": priorities}


@router.get("/by-category")
async def by_category(_: dict = Depends(require_roles("admin", "manager", "agent"))):
    pipeline = [{"$group": {"_id": "$category", "count": {"$sum": 1}}}, {"$sort": {"count": -1}}]
    return {"items": [{"category": row["_id"], "count": row["count"]} async for row in db.tickets.aggregate(pipeline)]}
