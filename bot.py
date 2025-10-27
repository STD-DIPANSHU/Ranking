import os
from telegram.ext import Application, CommandHandler
from core.handlers import leaderboard_command

BOT_TOKEN = os.getenv("BOT_TOKEN")

if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN environment variable not set!")

app = Application.builder().token(BOT_TOKEN).build()
app.add_handler(CommandHandler("leaderboard", leaderboard_command))

if __name__ == "__main__":
    print("✅ Bot started successfully...")
    app.run_polling()
