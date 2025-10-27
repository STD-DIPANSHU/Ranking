# core/handlers.py
from telegram import Update, InputMediaPhoto
from telegram.helpers import escape_markdown
from telegram.ext import ContextTypes
from core.leaderboard import get_leaderboard_data, create_leaderboard_image
from core.buttons import leaderboard_buttons  # make sure this exists and returns InlineKeyboardMarkup

# /leaderboard [today|week|month|all]
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
    # build safe caption (escape each username)
    lines = [f"🏆 *{title}*\n"]
    for i, r in enumerate(rows, start=1):
        safe = escape_markdown(str(r.get("username","Unknown")), version=2)
        lines.append(f"{i}. {safe} • {r.get('count',0)}")
    caption = "\n".join(lines)
    if len(caption) > 1000:
        caption = caption[:1000] + "…"

    image_buf.seek(0)
    await update.message.reply_photo(
        photo=image_buf,
        caption=caption,
        parse_mode="MarkdownV2",
        reply_markup=leaderboard_buttons(mode)
    )

# Callback handler for button clicks (callback_data should be "today","week","month","all")
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if query is None:
        return
    await query.answer()
    mode = query.data or "today"
    chat_id = query.message.chat.id

    rows, title = get_leaderboard_data(chat_id, mode)
    if not rows:
        try:
            await query.edit_message_caption(caption="No messages found yet 💬", reply_markup=leaderboard_buttons(mode))
        except:
            pass
        return

    image_buf = create_leaderboard_image(rows, title)
    image_buf.seek(0)

    # safe caption again
    lines = [f"🏆 *{title}*\n"]
    for i, r in enumerate(rows, start=1):
        safe = escape_markdown(str(r.get("username","Unknown")), version=2)
        lines.append(f"{i}. {safe} • {r.get('count',0)}")
    caption = "\n".join(lines)
    if len(caption) > 1000:
        caption = caption[:1000] + "…"

    media = InputMediaPhoto(media=image_buf)
    try:
        await query.edit_message_media(media=media)
    except Exception:
        # fallback: delete & send new message
        try:
            await query.message.delete()
        except:
            pass
        await context.bot.send_photo(chat_id=chat_id, photo=image_buf, caption=caption, parse_mode="MarkdownV2", reply_markup=leaderboard_buttons(mode))
        return

    try:
        await query.edit_message_caption(caption=caption, parse_mode="MarkdownV2", reply_markup=leaderboard_buttons(mode))
    except:
        # fallback to plain message
        await context.bot.send_message(chat_id=chat_id, text=caption)
