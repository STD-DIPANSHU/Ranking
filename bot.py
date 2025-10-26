from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler, filters
from core.handlers import start, leaderboard, my_stats, count_message, button_handler
from config.settings import BOT_TOKEN

def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("leaderboard", leaderboard))
    app.add_handler(CommandHandler("mystats", my_stats))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, count_message))
    app.add_handler(CallbackQueryHandler(button_handler, pattern="^view_"))

    print("🚀 Bot running...")
    app.run_polling()

if __name__ == "__main__":
    main()
