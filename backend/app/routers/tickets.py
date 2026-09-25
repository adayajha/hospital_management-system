from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Query, status
from bson import ObjectId
from pymongo import ReturnDocument
from ..database import db
from ..dependencies import get_current_user, require_roles, serialize
from ..schemas import Assignment, CommentCreate, StatusUpdate, TicketCreate, TicketStatus, TicketUpdate

router = APIRouter(prefix="/tickets", tags=["Tickets"])


def valid_id(value: str, label: str = "id") -> ObjectId:
    if not ObjectId.is_valid(value):
        raise HTTPException(status_code=400, detail=f"Invalid {label}")
    return ObjectId(value)


async def activity(ticket_id: ObjectId, actor: dict, action: str, details: str = "") -> None:
    await db.ticket_activities.insert_one({"ticket_id": ticket_id, "actor_id": actor["id"], "actor_name": actor["full_name"], "action": action, "details": details, "created_at": datetime.now(timezone.utc)})


async def get_ticket_or_404(ticket_id: str) -> dict:
    ticket = await db.tickets.find_one({"_id": valid_id(ticket_id, "ticket id")})
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    return ticket


def can_view(ticket: dict, user: dict) -> bool:
    return user["role"] in {"admin", "agent"} or ticket["created_by"] == user["id"] or (user["role"] == "manager" and ticket.get("department_id") == user.get("department_id"))


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_ticket(payload: TicketCreate, user: dict = Depends(get_current_user)):
    department_id = payload.department_id or user.get("department_id")
    if not department_id:
        raise HTTPException(status_code=422, detail="A department is required")
    if not ObjectId.is_valid(department_id) or not await db.departments.find_one({"_id": ObjectId(department_id)}):
        raise HTTPException(status_code=422, detail="Valid department is required")
    sequence = await db.counters.find_one_and_update({"_id": "ticket"}, {"$inc": {"value": 1}}, upsert=True, return_document=ReturnDocument.AFTER)
    number = f"HSRS-{datetime.now().year}-{sequence['value']:05d}"
    ticket = {**payload.model_dump(), "priority": payload.priority.value, "department_id": department_id, "ticket_number": number, "status": "open", "created_by": user["id"], "assigned_to": None, "resolution_note": None, "created_at": datetime.now(timezone.utc), "updated_at": datetime.now(timezone.utc)}
    result = await db.tickets.insert_one(ticket)
    await activity(result.inserted_id, user, "created", "Support request created")
    return {"ticket": serialize(await db.tickets.find_one({"_id": result.inserted_id}))}


@router.get("")
async def list_tickets(status_filter: TicketStatus | None = Query(None, alias="status"), priority: str | None = None, department_id: str | None = None, page: int = Query(1, ge=1), limit: int = Query(20, ge=1, le=100), user: dict = Depends(get_current_user)):
    query: dict = {}
    if user["role"] == "requester": query["created_by"] = user["id"]
    elif user["role"] == "manager": query["department_id"] = user.get("department_id")
    elif user["role"] == "agent": query["$or"] = [{"assigned_to": user["id"]}, {"assigned_to": None}]
    if status_filter: query["status"] = status_filter.value
    if priority: query["priority"] = priority
    if department_id and user["role"] in {"admin", "agent"}: query["department_id"] = department_id
    total = await db.tickets.count_documents(query)
    cursor = db.tickets.find(query).sort("created_at", -1).skip((page - 1) * limit).limit(limit)
    return {"items": [serialize(item) async for item in cursor], "page": page, "limit": limit, "total": total}


@router.get("/{ticket_id}")
async def ticket_detail(ticket_id: str, user: dict = Depends(get_current_user)):
    ticket = await get_ticket_or_404(ticket_id)
    if not can_view(ticket, user): raise HTTPException(status_code=403, detail="Ticket access denied")
    oid = ticket["_id"]
    comments_query = {"ticket_id": oid}
    if user["role"] == "requester": comments_query["internal"] = False
    return {"ticket": serialize(ticket), "comments": [serialize(x) async for x in db.ticket_comments.find(comments_query).sort("created_at", 1)], "activities": [serialize(x) async for x in db.ticket_activities.find({"ticket_id": oid}).sort("created_at", 1)]}


@router.patch("/{ticket_id}")
async def update_ticket(ticket_id: str, payload: TicketUpdate, user: dict = Depends(get_current_user)):
    ticket = await get_ticket_or_404(ticket_id)
    if ticket["created_by"] != user["id"] or ticket["status"] not in {"open", "reopened"}:
        raise HTTPException(status_code=403, detail="Only the requester may edit an open ticket")
    changes = payload.model_dump(exclude_none=True)
    if "priority" in changes: changes["priority"] = changes["priority"].value
    changes["updated_at"] = datetime.now(timezone.utc)
    await db.tickets.update_one({"_id": ticket["_id"]}, {"$set": changes})
    await activity(ticket["_id"], user, "updated", "Request details updated")
    return {"ticket": serialize(await db.tickets.find_one({"_id": ticket["_id"]}))}


@router.patch("/{ticket_id}/assign")
async def assign_ticket(ticket_id: str, payload: Assignment, user: dict = Depends(require_roles("admin", "agent", "manager"))):
    ticket = await get_ticket_or_404(ticket_id)
    agent = await db.users.find_one({"_id": valid_id(payload.agent_id, "agent id"), "role": "agent", "is_active": True})
    if not agent: raise HTTPException(status_code=422, detail="Active support agent not found")
    await db.tickets.update_one({"_id": ticket["_id"]}, {"$set": {"assigned_to": payload.agent_id, "status": "assigned", "updated_at": datetime.now(timezone.utc)}})
    await activity(ticket["_id"], user, "assigned", f"Assigned to {agent['full_name']}")
    return {"message": "Ticket assigned"}


@router.patch("/{ticket_id}/status")
async def change_status(ticket_id: str, payload: StatusUpdate, user: dict = Depends(get_current_user)):
    ticket = await get_ticket_or_404(ticket_id)
    if user["role"] not in {"admin", "agent"} and not (user["role"] == "requester" and ticket["created_by"] == user["id"] and payload.status == TicketStatus.reopened):
        raise HTTPException(status_code=403, detail="Status change is not permitted")
    if user["role"] == "agent" and ticket.get("assigned_to") not in {None, user["id"]}:
        raise HTTPException(status_code=403, detail="Ticket is assigned to another agent")
    changes = {"status": payload.status.value, "updated_at": datetime.now(timezone.utc)}
    if payload.status == TicketStatus.resolved:
        if not payload.resolution_note: raise HTTPException(status_code=422, detail="Resolution note is required")
        changes.update({"resolution_note": payload.resolution_note, "resolved_at": datetime.now(timezone.utc)})
    if payload.status == TicketStatus.closed: changes["closed_at"] = datetime.now(timezone.utc)
    await db.tickets.update_one({"_id": ticket["_id"]}, {"$set": changes})
    await activity(ticket["_id"], user, "status_changed", f"Status changed to {payload.status.value}")
    return {"message": "Ticket status updated"}


@router.post("/{ticket_id}/comments", status_code=status.HTTP_201_CREATED)
async def add_comment(ticket_id: str, payload: CommentCreate, user: dict = Depends(get_current_user)):
    ticket = await get_ticket_or_404(ticket_id)
    if not can_view(ticket, user): raise HTTPException(status_code=403, detail="Ticket access denied")
    if payload.internal and user["role"] not in {"admin", "agent", "manager"}: raise HTTPException(status_code=403, detail="Internal comments are for staff only")
    comment = {"ticket_id": ticket["_id"], "author_id": user["id"], "author_name": user["full_name"], **payload.model_dump(), "created_at": datetime.now(timezone.utc)}
    result = await db.ticket_comments.insert_one(comment)
    await activity(ticket["_id"], user, "commented", "Added a comment")
    return {"comment": serialize(await db.ticket_comments.find_one({"_id": result.inserted_id}))}
