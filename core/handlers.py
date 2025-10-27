from telegram import Update
from telegram.ext import ContextTypes
from core.leaderboard import generate_leaderboard_image


async def leaderboard_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle /leaderboard command.
    Generates leaderboard image and sends it to the user.
    """
    try:
        image_buffer = await generate_leaderboard_image()
        await update.message.reply_photo(photo=image_buffer, caption="Here’s the current leaderboard 🏅")
    except Exception as e:
        await update.message.reply_text(f"⚠️ Error generating leaderboard: {e}")


async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle button callbacks (if any for leaderboard interaction).
    """
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(text="Callback received ✅")
