from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler
from core.handlers import leaderboard_command, callback_handler

app = ApplicationBuilder().token("BOT_TOKEN").build()

app.add_handler(CommandHandler("leaderboard", leaderboard_command))
app.add_handler(CallbackQueryHandler(callback_handler))

app.run_polling()
