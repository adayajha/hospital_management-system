from contextlib import asynccontextmanager
from datetime import datetime, timezone
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .database import close_database, db, initialise_database
from .security import hash_password
from .routers import auth, departments, reports, tickets, users


async def seed_data() -> None:
    if not await db.users.find_one({"email": "admin@hospital.local"}):
        await db.users.insert_one({"full_name": "System Administrator", "email": "admin@hospital.local", "password_hash": hash_password("Admin123!"), "role": "admin", "department_id": None, "is_active": True, "created_at": datetime.now(timezone.utc)})
    if await db.departments.count_documents({}) == 0:
        await db.departments.insert_many([{"name": name, "code": code, "created_at": datetime.now(timezone.utc)} for name, code in [("Information Technology", "IT"), ("Facilities", "FAC"), ("Intensive Care Unit", "ICU")]])


@asynccontextmanager
async def lifespan(_: FastAPI):
    await initialise_database()
    await seed_data()
    yield
    await close_database()


app = FastAPI(title="Hospital Support Request System API", version="1.0.0", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=["http://localhost:5173"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])
app.include_router(auth.router, prefix="/api/v1")
app.include_router(departments.router, prefix="/api/v1")
app.include_router(users.router, prefix="/api/v1")
app.include_router(tickets.router, prefix="/api/v1")
app.include_router(reports.router, prefix="/api/v1")


@app.get("/health", tags=["System"])
async def health():
    return {"status": "healthy"}
