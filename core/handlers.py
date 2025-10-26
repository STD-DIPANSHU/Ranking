from telegram import Update, InputMediaPhoto
from telegram.ext import ContextTypes
from utils.db import messages
from core.leaderboard import get_leaderboard_data, create_leaderboard_image
from core.buttons import leaderboard_buttons
from datetime import datetime

# ✅ Start command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Welcome to *ChatFight Bot!* 🥊\n\n"
        "Type /leaderboard to see who's most active in this chat!\n\n"
        "Commands:\n"
        "• /leaderboard today — Show today's stats\n"
        "• /leaderboard week — Show weekly stats\n"
        "• /leaderboard month — Show monthly stats\n"
        "• /leaderboard all — Show all-time stats\n"
        "• /mystats — See your personal score",
        parse_mode="Markdown"
    )

# ✅ My stats command
async def my_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    chat = update.effective_chat
    all_data = list(messages.find({"chat_id": chat.id, "user_id": user.id}))
    total = sum(item.get("count", 0) for item in all_data)
    if total == 0:
        await update.message.reply_text("No messages found yet 💤")
        return

    today = datetime.utcnow().strftime("%Y-%m-%d")
    today_doc = messages.find_one({"chat_id": chat.id, "user_id": user.id, "date": today})
    today_count = today_doc.get("count", 0) if today_doc else 0

    await update.message.reply_text(
        f"📊 *Your Stats*\n\n"
        f"👤 {user.first_name or 'User'}\n"
        f"💬 Messages today: {today_count}\n"
        f"🔥 Total messages: {total}",
        parse_mode="Markdown"
    )

# ✅ Message counting
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

# ✅ Leaderboard command
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

# ✅ Button callbacks
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    mode = query.data.split("_")[1]
    chat_id = query.message.chat.id
    rows, title = get_leaderboard_data(chat_id, mode)
    bio = create_leaderboard_image(rows, title)
    caption = f"🏆 *{title}*\n\n" + "\n".join(
        [f"{i+1}. {r['username']} • {r['total']}" for i, r in enumerate(rows)]
    ) + f"\n\n📊 Total users shown: {len(rows)}"

    await query.edit_message_media(media=InputMediaPhoto(media=bio))
    await query.edit_message_caption(
        caption=caption, parse_mode="Markdown", reply_markup=leaderboard_buttons(mode)
    )
