from motor.motor_asyncio import AsyncIOMotorClient
import datetime
from config.settings import MONGO_URL

client = AsyncIOMotorClient(MONGO_URL)
db = client["chatfight_db"]
messages = db["messages"]

async def add_message(chat_id: int, user_id: int, user_name: str):
    """Store message count"""
    today = datetime.datetime.utcnow().date()
    week = today.isocalendar().week

    await messages.update_one(
        {"chat_id": chat_id, "user_id": user_id},
        {
            "$inc": {
                "overall": 1,
                f"daily.{today.isoformat()}": 1,
                f"weekly.{week}": 1
            },
            "$set": {"name": user_name}
        },
        upsert=True
    )

async def get_top_users(chat_id: int, scope: str):
    """Return top 10 users according to scope (overall/today/week)"""
    today = datetime.datetime.utcnow().date()
    week = today.isocalendar().week

    cursor = None
    if scope == "overall":
        cursor = messages.find({"chat_id": chat_id}).sort("overall", -1).limit(10)
    elif scope == "today":
        cursor = messages.find({"chat_id": chat_id}).sort(f"daily.{today.isoformat()}", -1).limit(10)
    elif scope == "week":
        cursor = messages.find({"chat_id": chat_id}).sort(f"weekly.{week}", -1).limit(10)
    else:
        return []

    data = []
    async for doc in cursor:
        count = (
            doc.get("overall", 0)
            if scope == "overall" else
            doc.get("daily", {}).get(today.isoformat(), 0)
            if scope == "today" else
            doc.get("weekly", {}).get(week, 0)
        )
        data.append({
            "name": doc.get("name", "Unknown"),
            "count": count
        })
    return data
