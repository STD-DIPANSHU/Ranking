# ================================
# ChatFight Bot — Handlers
# ================================
from telegram import Update, InputMediaPhoto
from telegram.ext import ContextTypes
from telegram.helpers import escape_markdown
from io import BytesIO

from core.leaderboard import create_leaderboard_image, get_leaderboard_data
from core.buttons import leaderboard_buttons
from utils.db import messages_collection


# ================================
# COUNT MESSAGE
# ================================
async def count_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Tracks each user's message count per day"""
    if update.effective_chat.type not in ["group", "supergroup"]:
        return

    user = update.effective_user
    chat = update.effective_chat
    today = context.application.bot_data.get("date", None)

    from datetime import datetime
    now = datetime.utcnow().strftime("%Y-%m-%d")

    messages_collection.update_one(
        {"chat_id": chat.id, "user_id": user.id, "date": now},
        {"$inc": {"count": 1}, "$set": {"username": user.username or user.first_name}},
        upsert=True,
    )


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

    image_buf = create_leaderboard_image(rows, title)

    # Safely format text
    lines = [f"🏆 *{title}*\n"]
    for i, r in enumerate(rows, start=1):
        safe_user = escape_markdown(str(r.get("username", "User")), version=2)
        lines.append(f"{i}. {safe_user} • {r.get('total', 0)}")
    caption_text = "\n".join(lines) + f"\n\n📊 Total users shown: {len(rows)}"

    image_buf.seek(0)
    await context.bot.send_photo(
        chat_id=chat_id,
        photo=image_buf,
        caption=caption_text,
        parse_mode="MarkdownV2",
        reply_markup=leaderboard_buttons(mode)
    )


# ================================
# INLINE BUTTON HANDLER
# ================================
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data or ""

    try:
        mode = data.split("_", 1)[1]
    except Exception:
        mode = "today"

    chat_id = query.message.chat_id
    rows, title = get_leaderboard_data(chat_id, mode)
    if not rows:
        await query.edit_message_caption("No data found 💬", reply_markup=leaderboard_buttons(mode))
        return

    image_buf = create_leaderboard_image(rows, title)
    image_buf.seek(0)

    lines = [f"🏆 *{title}*\n"]
    for i, r in enumerate(rows, start=1):
        safe_user = escape_markdown(str(r.get("username", "User")), version=2)
        lines.append(f"{i}. {safe_user} • {r.get('total', 0)}")
    caption_text = "\n".join(lines) + f"\n\n📊 Total users shown: {len(rows)}"

    media = InputMediaPhoto(media=image_buf)
    try:
        await query.edit_message_media(media=media)
        await query.edit_message_caption(
            caption=caption_text,
            parse_mode="MarkdownV2",
            reply_markup=leaderboard_buttons(mode)
        )
    except Exception:
        await context.bot.send_photo(
            chat_id=chat_id,
            photo=image_buf,
            caption=caption_text,
            parse_mode="MarkdownV2",
            reply_markup=leaderboard_buttons(mode)
        )


# ================================
# START + MYSTATS COMMANDS
# ================================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "👋 *Welcome to ChatFight Stats Bot!*\n\n"
        "Track your group activity with daily, weekly, and all-time leaderboards.\n\n"
        "📜 Commands:\n"
        "`/leaderboard today` — Today’s stats\n"
        "`/leaderboard week` — Weekly stats\n"
        "`/leaderboard all` — All-time stats\n"
        "`/mystats` — See your personal messages\n\n"
        "Add me to your group and start chatting 💬"
    )
    await update.message.reply_text(text, parse_mode="Markdown")


async def my_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    user = update.effective_user

    data = list(messages_collection.find({"chat_id": chat_id, "user_id": user.id}))
    total = sum(d.get("count", 0) for d in data)
    days = len(set(d["date"] for d in data))

    reply = f"📈 *Your Stats, {user.first_name}*\n\n💬 Messages: {total}\n📅 Active Days: {days}"
    await update.message.reply_text(reply, parse_mode="Markdown")
