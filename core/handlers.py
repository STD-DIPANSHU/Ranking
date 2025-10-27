from telegram import Update, InputFile, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes
from core.leaderboard import generate_leaderboard_image

async def leaderboard_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    scope = "overall"

    image = await generate_leaderboard_image(scope, chat_id)
    if image is None:
        await update.message.reply_text("No data yet 😅")
        return

    buttons = [
        [InlineKeyboardButton("🏆 Overall", callback_data="scope_overall"),
         InlineKeyboardButton("📅 Today", callback_data="scope_today"),
         InlineKeyboardButton("📆 Week", callback_data="scope_week")]
    ]
    await update.message.reply_photo(
        photo=InputFile(image, filename="leaderboard.png"),
        caption="📊 *Leaderboard*",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(buttons)
    )

async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    scope = query.data.replace("scope_", "")
    chat_id = query.message.chat_id

    image = await generate_leaderboard_image(scope, chat_id)
    if image is None:
        await query.answer("No data yet")
        return

    await query.message.edit_media(
        media=InputFile(image, filename="leaderboard.png")
    )
    await query.answer(f"Showing {scope} leaderboard ✅")
