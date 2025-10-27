# utils/db.py
from pymongo import MongoClient
import os
from datetime import datetime

MONGO_URL = os.getenv("MONGO_URL")
client = MongoClient(MONGO_URL) if MONGO_URL else MongoClient()
db = client["chatfight_bot"]
messages_collection = db["messages"]

def increment_message_count(chat_id: int, user_id: int, username: str):
    date = datetime.utcnow().strftime("%Y-%m-%d")
    messages_collection.update_one(
        {"chat_id": chat_id, "user_id": user_id, "date": date},
        {"$inc": {"count": 1}, "$set": {"username": username}},
        upsert=True,
    )

def get_leaderboard_from_db(query: dict):
    """
    query: a Mongo-style dict for date/chat_id filter, e.g. {"chat_id": 123, "date": "2025-10-26"}
    returns: list of dicts: [{"username": "...", "count": N}, ...]
    """
    pipeline = [
        {"$match": query},
        {"$group": {"_id": "$username", "count": {"$sum": "$count"}}},
        {"$sort": {"count": -1}},
        {"$limit": 10},
    ]
    data = list(messages_collection.aggregate(pipeline))
    # normalize
    return [{"username": d["_id"] or "Unknown", "count": d["count"]} for d in data]

def get_user_stats(chat_id: int, user_id: int):
    docs = list(messages_collection.find({"chat_id": chat_id, "user_id": user_id}))
    total = sum(d.get("count", 0) for d in docs)
    days = len(set(d["date"] for d in docs))
    return {"total": total, "days": days}
