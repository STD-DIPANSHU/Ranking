# =========================================
# 📂 utils/db.py
# =========================================

from pymongo import MongoClient
import os

# ================================
# DATABASE CONNECTION
# ================================
MONGO_URL = os.getenv("MONGO_URL")
client = MongoClient(MONGO_URL)
db = client["chatfight_bot"]
messages_collection = db["messages"]

# ================================
# 💾 Message Counting
# ================================
def save_message(chat_id: int, user_id: int, username: str, date: str):
    messages_collection.update_one(
        {"chat_id": chat_id, "user_id": user_id, "date": date},
        {"$inc": {"count": 1}, "$set": {"username": username}},
        upsert=True,
    )

# ================================
# 📊 Leaderboard Data Fetch
# ================================
def get_leaderboard_from_db(query: dict):
    pipeline = [
        {"$match": query},
        {"$group": {"_id": "$username", "count": {"$sum": "$count"}}},
        {"$sort": {"count": -1}},
        {"$limit": 10},
    ]
    data = list(messages_collection.aggregate(pipeline))
    return [{"username": d["_id"], "count": d["count"]} for d in data]

# ================================
# 🧍‍♂️ Personal Stats
# ================================
def get_user_stats(chat_id: int, user_id: int):
    data = list(messages_collection.find({"chat_id": chat_id, "user_id": user_id}))
    total = sum(d.get("count", 0) for d in data)
    days = len(set(d["date"] for d in data))
    return total, days
