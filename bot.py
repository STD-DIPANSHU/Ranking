# ================================
# ChatFight-Style Telegram Stats Bot (Enhanced)
# Author: STD BHAI x GPT-5 😎
# Deploy on: Heroku
# ================================

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters
from pymongo import MongoClient
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from io import BytesIO
import os

# ================================
# CONFIGURATION
# ================================
TOKEN = os.getenv("BOT_TOKEN")  # Telegram bot token (Heroku config var)
MONGO_URL = os.getenv("MONGO_URL")  # MongoDB URL (Heroku config var)

client = MongoClient(MONGO_URL)
db = client["chatfight_bot"]
messages = db["messages"]

# ================================
# MESSAGE COUNTER
# ================================
async def count_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type not in ["group", "supergroup"]:
        return

    user = update.effective_user
    chat = update.effective_chat
    now = datetime.utcnow().strftime("%Y-%m-%d")

    messages.update_one(
        {"chat_id": chat.id, "user_id": user.id, "date": now},
        {"$inc": {"count": 1}, "$set": {"username": user.username or user.first_name}},
        upsert=True,
    )

# ================================
# LEADERBOARD IMAGE CREATOR
# ================================
def create_leaderboard_image(rows, title="Leaderboard"):
    names = [r.get("username", "User") for r in rows][::-1]
    counts = [r.get("total", 0) for r in rows][::-1]
    total_users = len(names)

    plt.figure(figsize=(9, max(3, 0.7 * total_users)))
    ax = plt.gca()
    ax.set_facecolor("#0d0000")
    fig = plt.gcf()
    fig.patch.set_facecolor("#0d0000")

    bars = plt.barh(
        range(total_users),
        counts,
        color="#b30000",
        edgecolor="#ff3333",
        linewidth=1.5,
    )

    plt.yticks(range(total_users), names, fontsize=12, color="white", fontweight="bold")
    plt.xlabel("Messages", color="white", fontsize=12)
    plt.title(f"🏆 {title} 🏆", color="#ff6666", fontsize=16, fontweight="bold", pad=15)

    for spine in ax.spines.values():
        spine.set_visible(False)

    for bar, val in zip(bars, counts):
        ax.text(
            bar.get_width() + max(1, val * 0.02),
            bar.get_y() + bar.get_height() / 2,
            f"{val}",
            va="center",
            ha="left",
            color="#ffcccc",
            fontsize=11,
            fontweight="bold",
        )

    for bar in bars:
        rect = patches.Rectangle(
            (0, bar.get_y()),
            bar.get_width(),
            bar.get_height(),
            linewidth=0,
            edgecolor=None,
            facecolor="#ff0000",
            alpha=0.05,
        )
        ax.add_patch(rect)

    plt.grid(axis="x", color="#331111", linestyle="--", alpha=0.3)
    plt.tight_layout()

    bio = BytesIO()
    plt.savefig(bio, format="png", dpi=150, bbox_inches="tight", facecolor=fig.get_facecolor())
    plt.close()
    bio.seek(0)
    return bio

# ================================
# BUTTONS FUNCTION
# ================================
def leaderboard_buttons(current_view):
    buttons = [
        [
            InlineKeyboardButton(f"Overall {'✅' if current_view == 'all' else ''}", callback_data='view_all'),
            InlineKeyboardButton(f"Today {'✅' if current_view == 'today' else ''}", callback_data='view_today'),
        ],
        [
            InlineKeyboardButton(f"Week {'✅' if current_view == 'week' else ''}", callback_data='view_week'),
            InlineKeyboardButton(f"Month {'✅' if current_view == 'month' else ''}", callback_data='view_month'),
        ]
    ]
    return InlineKeyboardMarkup(buttons)

# ================================
# FETCH LEADERBOARD DATA
# ================================
def get_leaderboard_data(chat_id, mode):
    now = datetime.utcnow()

    if mode == "week":
        start_date = now - timedelta(days=7)
        title_text = "This Week's Leaderboard"
        query = {"chat_id": chat_id, "date": {"$gte": start_date.strftime("%Y-%m-%d")}}

    elif mode == "month":
        start_date = now - timedelta(days=30)
        title_text = "This Month's Leaderboard"
        query = {"chat_id": chat_id, "date": {"$gte": start_date.strftime("%Y-%m-%d")}}

    elif mode == "all":
        title_text = "All-Time Leaderboard"
        query = {"chat_id": chat_id}

    else:
        today = now.strftime("%Y-%m-%d")
        title_text = "Today's Leaderboard"
        query = {"chat_id": chat_id, "date": today}

    data = list(messages.aggregate([
        {"$match": query},
        {"$group": {"_id": "$username", "total": {"$sum": "$count"}}},
        {"$sort": {"total": -1}},
        {"$limit": 10},
    ]))

    rows = [{"username": d["_id"], "total": d["total"]} for d in data]
    return rows, title_text

# ================================
# LEADERBOARD COMMAND
# ================================
async def leaderboard(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    args = context.args
    mode = args[0].lower() if args else "today"

    rows, title_text = get_leaderboard_data(chat_id, mode)
    if not rows:
        await update.message.reply_text("No messages found yet. Start chatting! 💬")
        return

    bio = create_leaderboard_image(rows, title_text)

    # Text caption
    caption = f"🏆 *{title_text}*\n\n"
    for i, r in enumerate(rows, start=1):
        caption += f"{i}. {r['username']} • {r['total']}\n"
    caption += f"\n📊 Total users shown: {len(rows)}"

    await context.bot.send_photo(
        chat_id=chat_id,
        photo=bio,
        caption=caption,
        parse_mode="Markdown",
        reply_markup=leaderboard_buttons(mode)
    )

# ================================
# BUTTON CALLBACK HANDLER
# ================================
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    mode = query.data.split("_")[1]

    chat_id = query.message.chat_id
    rows, title_text = get_leaderboard_data(chat_id, mode)

    if not rows:
        await query.edit_message_caption(caption="No messages yet 💬")
        return

    bio = create_leaderboard_image(rows, title_text)

    caption = f"🏆 *{title_text}*\n\n"
    for i, r in enumerate(rows, start=1):
        caption += f"{i}. {r['username']} • {r['total']}\n"
    caption += f"\n📊 Total users shown: {len(rows)}"

    await query.edit_message_media(
        media={"type": "photo", "media": bio},
    )
    await query.edit_message_caption(
        caption=caption,
        parse_mode="Markdown",
        reply_markup=leaderboard_buttons(mode)
    )

# ================================
# PERSONAL STATS
# ================================
async def my_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    user = update.effective_user
    data = list(messages.find({"chat_id": chat_id, "user_id": user.id}))

    total = sum(d.get("count", 0) for d in data)
    days = len(set(d["date"] for d in data))

    reply = f"📈 *Your Stats, {user.first_name}*\n\n💬 Total Messages: {total}\n📅 Active Days: {days}"
    await update.message.reply_text(reply, parse_mode="Markdown")

# ================================
# START COMMAND
# ================================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "👋 *Welcome to ChatFight Stats Bot!*\n\n"
        "Track your group activity with daily, weekly, and total leaderboards.\n\n"
        "📜 Commands:\n"
        "`/top today` — Today’s leaderboard\n"
        "`/top week` — This week\n"
        "`/top month` — This month\n"
        "`/top all` — All time\n"
        "`/mystats` — Your message stats\n\n"
        "Add me to your group and start chatting! 💬"
    )
    await update.message.reply_text(text, parse_mode="Markdown")

# ================================
# MAIN ENTRY
# ================================
def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("mystats", my_stats))
    app.add_handler(CommandHandler("top", leaderboard))
    app.add_handler(CallbackQueryHandler(button_handler, pattern="^view_"))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, count_message))

    print("🚀 ChatFight Enhanced Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()
