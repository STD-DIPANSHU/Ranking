# =========================================
# 📂 core/buttons.py
# =========================================

from telegram import InlineKeyboardButton


def get_leaderboard_buttons(current_mode: str):
    """
    Returns 4 buttons for leaderboard modes with highlighting on the active one.
    """
    modes = ["today", "week", "month", "all"]
    labels = {
        "today": "🔥 Today",
        "week": "📅 Week",
        "month": "🗓️ Month",
        "all": "🏆 All Time",
    }

    buttons = [
        [
            InlineKeyboardButton(
                text=(f"✅ {labels[m]}" if m == current_mode else labels[m]),
                callback_data=m,
            )
            for m in modes
        ]
    ]
    return buttons
