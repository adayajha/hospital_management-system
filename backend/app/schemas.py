from datetime import datetime
from enum import Enum
from pydantic import BaseModel, EmailStr, Field


class Role(str, Enum):
    requester = "requester"
    agent = "agent"
    manager = "manager"
    admin = "admin"


class TicketStatus(str, Enum):
    open = "open"
    assigned = "assigned"
    in_progress = "in_progress"
    resolved = "resolved"
    closed = "closed"
    reopened = "reopened"


class Priority(str, Enum):
    low = "low"
    medium = "medium"
    high = "high"
    critical = "critical"


class UserCreate(BaseModel):
    full_name: str = Field(min_length=2, max_length=100)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    role: Role = Role.requester
    department_id: str | None = None


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class DepartmentCreate(BaseModel):
    name: str = Field(min_length=2, max_length=100)
    code: str = Field(min_length=2, max_length=15)


class TicketCreate(BaseModel):
    subject: str = Field(min_length=5, max_length=160)
    description: str = Field(min_length=10, max_length=5000)
    category: str = Field(pattern="^(equipment_issue|maintenance|it_issue|facility_request)$")
    priority: Priority = Priority.medium
    department_id: str | None = None


class TicketUpdate(BaseModel):
    subject: str | None = Field(default=None, min_length=5, max_length=160)
    description: str | None = Field(default=None, min_length=10, max_length=5000)
    priority: Priority | None = None


class Assignment(BaseModel):
    agent_id: str


class StatusUpdate(BaseModel):
    status: TicketStatus
    resolution_note: str | None = Field(default=None, max_length=3000)


class CommentCreate(BaseModel):
    message: str = Field(min_length=1, max_length=3000)
    internal: bool = False


class APIMessage(BaseModel):
    message: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
