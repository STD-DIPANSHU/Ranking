# =========================================
# 📂 core/handlers.py
# =========================================

from telegram import Update, InlineKeyboardMarkup
from telegram.ext import (
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
    ContextTypes,
)
from core.leaderboard import create_leaderboard_image, get_leaderboard_data
from core.buttons import get_leaderboard_buttons
from utils.db import increment_message_count, get_user_stats


# =========================================
# 🚀 START COMMAND
# =========================================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    await update.message.reply_text(
        f"👋 Welcome, {user.first_name}!\n\n"
        "This is *ChatFight Bot* — every message you send earns XP 💬⚡\n\n"
        "Use /leaderboard to see your ranking!",
        parse_mode="Markdown",
    )


# =========================================
# 🧠 COUNT MESSAGES
# =========================================
async def count_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if user and not user.is_bot:
        increment_message_count(user.id, user.first_name)


# =========================================
# 🏆 LEADERBOARD COMMAND
# =========================================
async def leaderboard(update: Update, context: ContextTypes.DEFAULT_TYPE):
    mode = "all"
    data = get_leaderboard_data(mode)
    if not data:
        await update.message.reply_text("No data available yet 😅")
        return

    # Create image
    image_path = create_leaderboard_image(data, mode)

    # Send image + buttons
    await update.message.reply_photo(
        photo=open(image_path, "rb"),
        caption=f"🏆 *Top ChatFighters ({mode.title()})*",
        reply_markup=InlineKeyboardMarkup(get_leaderboard_buttons(mode)),
        parse_mode="Markdown",
    )


# =========================================
# 💪 MY STATS COMMAND
# =========================================
async def my_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    stats = get_user_stats(user.id)
    if not stats:
        await update.message.reply_text("No stats found 😅 Start chatting!")
        return

    await update.message.reply_text(
        f"📊 *Your Stats*\n\n"
        f"👤 Name: {user.first_name}\n"
        f"💬 Messages: {stats['count']}\n"
        f"🏆 Rank: #{stats['rank']}",
        parse_mode="Markdown",
    )


# =========================================
# 🎯 BUTTON HANDLER
# =========================================
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    mode = query.data  # today/week/month/all
    data = get_leaderboard_data(mode)
    if not data:
        await query.edit_message_caption(
            caption="No data for this mode 😅", reply_markup=None
        )
        return

    image_path = create_leaderboard_image(data, mode)
    await query.edit_message_media(
        media={"type": "photo", "media": open(image_path, "rb")},
        reply_markup=InlineKeyboardMarkup(get_leaderboard_buttons(mode)),
    )
    await query.edit_message_caption(
        caption=f"🏆 *Top ChatFighters ({mode.title()})*",
        reply_markup=InlineKeyboardMarkup(get_leaderboard_buttons(mode)),
        parse_mode="Markdown",
    )


# =========================================
# 🧩 HANDLER SETUP FUNCTION
# =========================================
def register_handlers(application):
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("leaderboard", leaderboard))
    application.add_handler(CommandHandler("mystats", my_stats))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, count_message))
    application.add_handler(CallbackQueryHandler(button_handler))
