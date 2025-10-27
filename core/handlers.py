# core/handlers.py
from telegram import Update, InputMediaPhoto
from telegram.helpers import escape_markdown
from telegram.ext import ContextTypes
from core.leaderboard import get_leaderboard_data, create_leaderboard_image
from core.buttons import leaderboard_buttons
from utils.db import increment_message_count, get_user_stats

# =================== /start command ===================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    name = user.first_name if user else "User"
    text = (
        f"👋 Hello {name}!\n\n"
        f"Welcome to *ChatFight Leaderboard Bot* 🏆\n\n"
        f"Use /leaderboard to see who's most active.\n"
        f"Use /mystats to check your own stats.\n\n"
        f"Let's begin 🔥"
    )
    await update.message.reply_text(text, parse_mode="Markdown")

# =================== Count messages ===================
async def count_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    user = update.effective_user
    if not chat or not user:
        return
    if user.is_bot:
        return
    username = user.username or user.first_name or "User"
    increment_message_count(chat.id, user.id, username)

# =================== /mystats command ===================
async def my_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    user = update.effective_user
    if not chat or not user:
        return
    stats = get_user_stats(chat.id, user.id)
    total = stats.get("total", 0)
    days = stats.get("days", 0)
    avg = round(total / days, 2) if days else 0
    text = (
        f"📊 *Your Stats*\n\n"
        f"💬 Total Messages: *{total}*\n"
        f"📅 Active Days: *{days}*\n"
        f"⚡ Avg per Day: *{avg}*"
    )
    await update.message.reply_text(text, parse_mode="Markdown")

# =================== /leaderboard command ===================
async def leaderboard(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    if chat is None:
        return
    chat_id = chat.id
    args = context.args
    mode = args[0].lower() if args else "today"

    rows, title = get_leaderboard_data(chat_id, mode)
    if not rows:
        await update.message.reply_text("No messages found yet 💬")
        return

    image_buf = create_leaderboard_image(rows, title)
    lines = [f"🏆 *{title}*\n"]
    for i, r in enumerate(rows, start=1):
        safe = escape_markdown(str(r.get("username", "Unknown")), version=2)
        lines.append(f"{i}. {safe} • {r.get('count', 0)}")
    caption = "\n".join(lines)[:1000]

    await update.message.reply_photo(
        photo=image_buf,
        caption=caption,
        parse_mode="MarkdownV2",
        reply_markup=leaderboard_buttons(mode),
    )

# =================== Callback buttons ===================
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if query is None:
        return
    await query.answer()
    mode = query.data or "today"
    chat_id = query.message.chat.id

    rows, title = get_leaderboard_data(chat_id, mode)
    if not rows:
        await query.edit_message_caption(caption="No messages found yet 💬", reply_markup=leaderboard_buttons(mode))
        return

    image_buf = create_leaderboard_image(rows, title)
    lines = [f"🏆 *{title}*\n"]
    for i, r in enumerate(rows, start=1):
        safe = escape_markdown(str(r.get("username", "Unknown")), version=2)
        lines.append(f"{i}. {safe} • {r.get('count', 0)}")
    caption = "\n".join(lines)[:1000]

    media = InputMediaPhoto(media=image_buf)
    await query.edit_message_media(media=media)
    await query.edit_message_caption(
        caption=caption,
        parse_mode="MarkdownV2",
        reply_markup=leaderboard_buttons(mode),
    )
