# utils/db.py
from pymongo import MongoClient
from config.settings import MONGO_URL

client = MongoClient(MONGO_URL)
db = client["chatfight_db"]

# Ye collection sab jagah use hogi
messages_collection = db["messages"]

# Helper functions
def add_message(user_id, username):
    """User ke message count badhata hai"""
    messages_collection.update_one(
        {"user_id": user_id},
        {"$inc": {"count": 1}, "$set": {"username": username}},
        upsert=True
    )

def get_user_stats(user_id):
    """User ka total count return karta hai"""
    user = messages_collection.find_one({"user_id": user_id})
    return user["count"] if user else 0

def get_top_users(limit=10):
    """Top users return karta hai message count ke hisab se"""
    return list(messages_collection.find().sort("count", -1).limit(limit))
