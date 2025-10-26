# core/buttons.py
from telegram import InlineKeyboardButton, InlineKeyboardMarkup

def leaderboard_buttons(active_mode="daily"):
    buttons = [
        ("Daily 🕒", "daily"),
        ("Weekly 📅", "weekly"),
        ("Monthly 🏆", "monthly"),
        ("All Time 🌍", "all"),
    ]

    # ✅ Naya list create kar rahe hain (immutability problem fix)
    keyboard = [
        [
            InlineKeyboardButton(
                f"✅ {text}" if mode == active_mode else text,
                callback_data=f"leaderboard_{mode}"
            )
        ]
        for text, mode in buttons
    ]
    return InlineKeyboardMarkup(keyboard)
() in btn.callback_data:
                btn.text = f"✅ {btn.text}"

    return InlineKeyboardMarkup(buttons)
