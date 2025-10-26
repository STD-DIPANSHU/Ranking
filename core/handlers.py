from telegram import Update, InputMediaPhoto
from telegram.ext import ContextTypes
from utils.db import messages
from core.leaderboard import get_leaderboard_data, create_leaderboard_image
from core.buttons import leaderboard_buttons
from datetime import datetime

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
