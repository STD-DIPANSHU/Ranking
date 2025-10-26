# ================================
# ChatFight Bot — Inline Buttons
# ================================
from telegram import InlineKeyboardButton, InlineKeyboardMarkup

def leaderboard_buttons(active="today"):
    buttons = [
        [
            InlineKeyboardButton("⚡ Today", callback_data="leaderboard_today"),
            InlineKeyboardButton("🔥 Week", callback_data="leaderboard_week"),
        ],
        [
            InlineKeyboardButton("🌙 Month", callback_data="leaderboard_month"),
            InlineKeyboardButton("🏆 All Time", callback_data="leaderboard_all"),
        ]
    ]

    # Highlight active mode
    for row in buttons:
        for btn in row:
            if active.lower() in btn.callback_data:
                btn.text = f"✅ {btn.text}"

    return InlineKeyboardMarkup(buttons)
