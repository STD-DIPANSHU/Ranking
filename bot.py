#!/usr/bin/env python3
import os
import logging
from datetime import datetime, timedelta
from io import BytesIO

from pymongo import MongoClient
from dateutil import tz
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

import matplotlib.pyplot as plt
from PIL import Image

# ---------- Logging ----------
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# ---------- Config / Env ----------
TOKEN = os.environ.get("TELEGRAM_TOKEN")
MONGO_URI = os.environ.get("MONGO_URI")
if not TOKEN or not MONGO_URI:
    logger.error("TELEGRAM_TOKEN and MONGO_URI must be set in environment variables.")
    raise SystemExit("Set environment variables")

TZ = os.environ.get("BOT_TZ", "UTC")  # optional timezone, default UTC

# ---------- Database ----------
client = MongoClient(MONGO_URI)
db = client["chatstats_bot"]
counts = db["counts"]   # documents: { chat_id, user_id, username, date: "YYYY-MM-DD", count }
users = db["users"]     # optional user meta

# Helper: today's date string in bot timezone
def today_str(offset_days=0):
    tzinfo = tz.gettz(TZ)
    now = datetime.now(tzinfo) + timedelta(days=offset_days)
    return now.strftime("%Y-%m-%d")

# ---------- Message counting ----------
async def count_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message:
        return
    chat = update.effective_chat
    user = update.effective_user
    if not chat or chat.type == "private":
        # only count in groups/supergroups
        return
    date = today_str(0)
    chat_id = chat.id
    user_id = user.id
    username = user.full_name if not user.username else f"@{user.username}"
    # increment
    counts.update_one(
        {"chat_id": chat_id, "user_id": user_id, "date": date},
        {"$inc": {"count": 1}, "$set": {"username": username}},
        upsert=True,
    )

# ---------- Commands ----------
async def start_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "👋 Hello! I'm GroupStatsBot.\n\n"
        "I count messages in group and can show leaderboards.\n\n"
        "Commands:\n"
        "/mystats - your stats (today/week/overall)\n"
        "/top [today|week|overall] - show top users (default today)\n"
        "/help - this help\n\n"
        "Add me to the group and give me permission to read messages."
    )
    await update.message.reply_text(text)

async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await start_cmd(update, context)

# Stats for a user
async def mystats_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    user = update.effective_user
    if chat.type == "private":
        await update.message.reply_text("Add me into a group and check stats there.")
        return
    chat_id = chat.id
    user_filter = {"chat_id": chat_id, "user_id": user.id}

    # today
    today = today_str(0)
    doc = counts.find_one({**user_filter, "date": today})
    today_count = doc["count"] if doc else 0

    # week: get last 7 days including today
    tzinfo = tz.gettz(TZ)
    now = datetime.now(tzinfo)
    dates = [(now - timedelta(days=i)).strftime("%Y-%m-%d") for i in range(7)]
    cursor = counts.find({"chat_id": chat_id, "user_id": user.id, "date": {"$in": dates}})
    week_total = sum([c["count"] for c in cursor])

    # overall
    cursor2 = counts.find({"chat_id": chat_id, "user_id": user.id})
    overall = sum([c["count"] for c in cursor2])

    text = f"📊 Stats for {user.full_name or user.username}:\n\n"
    text += f"• Today: {today_count}\n"
    text += f"• Last 7 days: {week_total}\n"
    text += f"• Overall (since bot added): {overall}\n"
    await update.message.reply_text(text)

# Top leaderboard text or image
def aggregate_top(chat_id, mode="today", limit=10):
    tzinfo = tz.gettz(TZ)
    now = datetime.now(tzinfo)

    if mode == "today":
        date = now.strftime("%Y-%m-%d")
        pipeline = [
            {"$match": {"chat_id": chat_id, "date": date}},
            {"$group": {"_id": "$user_id", "username": {"$first": "$username"}, "total": {"$sum": "$count"}}},
            {"$sort": {"total": -1}},
            {"$limit": limit},
        ]
    elif mode == "week":
        dates = [(now - timedelta(days=i)).strftime("%Y-%m-%d") for i in range(7)]
        pipeline = [
            {"$match": {"chat_id": chat_id, "date": {"$in": dates}}},
            {"$group": {"_id": "$user_id", "username": {"$first": "$username"}, "total": {"$sum": "$count"}}},
            {"$sort": {"total": -1}},
            {"$limit": limit},
        ]
    else:  # overall
        pipeline = [
            {"$match": {"chat_id": chat_id}},
            {"$group": {"_id": "$user_id", "username": {"$first": "$username"}, "total": {"$sum": "$count"}}},
            {"$sort": {"total": -1}},
            {"$limit": limit},
        ]
    return list(counts.aggregate(pipeline))

def create_leaderboard_image(rows, title="Leaderboard"):
    # rows: list of dicts with 'username' and 'total'
    names = [r.get("username", "User") for r in rows][::-1]  # reverse for horizontal bar
    counts_list = [r.get("total", 0) for r in rows][::-1]

    plt.figure(figsize=(8, max(2, 0.5 * len(names) + 1)))
    bars = plt.barh(range(len(names)), counts_list)
    plt.yticks(range(len(names)), names, fontsize=10)
    plt.xlabel("Messages")
    plt.title(title)
    for i, v in enumerate(counts_list):
        plt.text(v + max(1, v*0.02), i, str(v), va="center")
    plt.tight_layout()

    bio = BytesIO()
    plt.savefig(bio, format="png")
    plt.close()
    bio.seek(0)
    return bio

async def top_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    if chat.type == "private":
        await update.message.reply_text("Add me into a group and run this command there.")
        return
    mode = "today"
    if context.args:
        arg = context.args[0].lower()
        if arg in ("today", "week", "overall"):
            mode = arg
    chat_id = chat.id
    rows = aggregate_top(chat_id, mode=mode, limit=10)
    if not rows:
        await update.message.reply_text("No data yet.")
        return

    # send image leaderboard
    title_text = {"today": "Today's Leaderboard", "week": "This Week's Leaderboard", "overall": "Overall Leaderboard"}[mode]
    bio = create_leaderboard_image(rows, title=title_text)
    await context.bot.send_photo(chat_id=chat_id, photo=bio, caption=title_text)

# ---------- Main ----------
def main():
    app = ApplicationBuilder().token(TOKEN).build()
    # handlers
    app.add_handler(CommandHandler("start", start_cmd))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(CommandHandler("mystats", mystats_cmd))
    app.add_handler(CommandHandler("top", top_cmd))

    # message counter (count text, stickers, photos - you can extend)
    app.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND, count_message))

    logger.info("Bot starting polling...")
    app.run_polling()

if __name__ == "__main__":
    main()
