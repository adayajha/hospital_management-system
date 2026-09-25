from motor.motor_asyncio import AsyncIOMotorClient
from .config import settings

client = AsyncIOMotorClient(settings.mongo_url)
db = client[settings.mongo_db]


async def initialise_database() -> None:
    await db.users.create_index("email", unique=True)
    await db.tickets.create_index("ticket_number", unique=True)
    await db.tickets.create_index([("department_id", 1), ("status", 1), ("created_at", -1)])
    await db.tickets.create_index([("assigned_to", 1), ("status", 1)])


async def close_database() -> None:
    client.close()
