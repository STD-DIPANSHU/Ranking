# ================================
# ChatFight Telegram Leaderboard Bot (v3 Fixed)
# ================================

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InputMediaPhoto
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters
from pymongo import MongoClient
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from io import BytesIO
import os

# ================================
# CONFIG
# ================================
TOKEN = os.getenv("BOT_TOKEN")
MONGO_URL = os.getenv("MONGO_URL")

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
# IMAGE CREATOR
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

    bars = plt.barh(range(total_users), counts, color="#b30000", edgecolor="#ff3333", linewidth=1.5)
    plt.yticks(range(total_users), names, fontsize=12, color="white", fontweight="bold")
    plt.xlabel("Messages", color="white", fontsize=12)
    plt.title(f"🏆 {title} 🏆", color="#ff6666", fontsize=16, fontweight="bold", pad=15)

    for spine in ax.spines.values():
        spine.set_visible(False)
    for bar, val in zip(bars, counts):
        ax.text(bar.get_width() + 0.5, bar.get_y() + bar.get_height() / 2, f"{val}", va="center", ha="left",
                color="#ffcccc", fontsize=11, fontweight="bold")
    plt.grid(axis="x", color="#331111", linestyle="--", alpha=0.3)
    plt.tight_layout()

    bio = BytesIO()
    plt.savefig(bio, format="png", dpi=150, bbox_inches="tight", facecolor=fig.get_facecolor())
    plt.close()
    bio.seek(0)
    return bio

# ================================
# BUTTONS
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
# FETCH DATA
# ================================
def get_leaderboard_data(chat_id, mode):
    now = datetime.utcnow()
    if mode == "week":
        start_date = now - timedelta(days=7)
        query = {"chat_id": chat_id, "date": {"$gte": start_date.strftime("%Y-%m-%d")}}
        title = "This Week's Leaderboard"
    elif mode == "month":
        start_date = now - timedelta(days=30)
        query = {"chat_id": chat_id, "date": {"$gte": start_date.strftime("%Y-%m-%d")}}
        title = "This Month's Leaderboard"
    elif mode == "all":
        query = {"chat_id": chat_id}
        title = "All-Time Leaderboard"
    else:
        today = now.strftime("%Y-%m-%d")
        query = {"chat_id": chat_id, "date": today}
        title = "Today's Leaderboard"

    data = list(messages.aggregate([
        {"$match": query},
        {"$group": {"_id": "$username", "total": {"$sum": "$count"}}},
        {"$sort": {"total": -1}},
        {"$limit": 10}
    ]))
    rows = [{"username": d["_id"], "total": d["total"]} for d in data]
    return rows, title

# ================================
# LEADERBOARD COMMAND
# ================================
async def leaderboard(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    args = context.args
    mode = args[0].lower() if args else "today"
    rows, title = get_leaderboard_data(chat_id, mode)

    if not rows:
        await update.message.reply_text("No messages found yet 💬")
        return

    bio = create_leaderboard_image(rows, title)
    caption = f"🏆 *{title}*\n\n" + "\n".join(
        [f"{i+1}. {r['username']} • {r['total']}" for i, r in enumerate(rows)]
    ) + f"\n\n📊 Total users shown: {len(rows)}"

    await context.bot.send_photo(
        chat_id=chat_id,
        photo=bio,
        caption=caption,
        parse_mode="Markdown",
        reply_markup=leaderboard_buttons(mode)
    )

# ================================
# BUTTON HANDLER (FIXED)
# ================================
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    mode = query.data.split("_")[1]
    chat_id = query.message.chat.id

    rows, title = get_leaderboard_data(chat_id, mode)
    if not rows:
        await query.edit_message_caption(caption="No messages found yet 💬")
        return

    bio = create_leaderboard_image(rows, title)
    caption = f"🏆 *{title}*\n\n" + "\n".join(
        [f"{i+1}. {r['username']} • {r['total']}" for i, r in enumerate(rows)]
    ) + f"\n\n📊 Total users shown: {len(rows)}"

    await query.edit_message_media(
        media=InputMediaPhoto(media=bio),
    )
    await query.edit_message_caption(
        caption=caption,
        parse_mode="Markdown",
        reply_markup=leaderboard_buttons(mode)
    )

# ================================
# START COMMAND
# ================================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Welcome to ChatFight Stats Bot!\n"
        "Track your group activity with live leaderboards.\n\n"
        "Commands:\n"
        "/leaderboard — Show today's leaderboard\n"
        "/leaderboard week — Weekly stats\n"
        "/leaderboard month — Monthly stats\n"
        "/leaderboard all — All-time\n"
        "/mystats — Your own stats"
    )

# ================================
# USER STATS
# ================================
async def my_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    user = update.effective_user
    data = list(messages.find({"chat_id": chat_id, "user_id": user.id}))
    total = sum(d.get("count", 0) for d in data)
    days = len(set(d["date"] for d in data))
    await update.message.reply_text(f"📈 Stats for {user.first_name}\n\n💬 {total} messages\n📅 {days} days active")

# ================================
# MAIN
# ================================
def main():
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("leaderboard", leaderboard))
    app.add_handler(CommandHandler("mystats", my_stats))
    app.add_handler(CallbackQueryHandler(button_handler, pattern="^view_"))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, count_message))
    print("🚀 Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()
