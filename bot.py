import os
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from core.handlers import leaderboard_command

BOT_TOKEN = os.getenv("BOT_TOKEN")

if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN environment variable not set!")

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Bot working ✅\nUse /leaderboard")

app = Application.builder().token(BOT_TOKEN).build()

app.add_handler(CommandHandler("start", start_command))   # ✅ ADD THIS
app.add_handler(CommandHandler("leaderboard", leaderboard_command))

if __name__ == "__main__":
    print("✅ Bot started successfully...")
    app.run_polling()
