from pymongo import MongoClient
from config.settings import MONGO_URL

client = MongoClient(MONGO_URL)
db = client["chatfight_bot"]
messages = db["messages"]
