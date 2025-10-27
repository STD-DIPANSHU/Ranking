# core/buttons.py
from telegram import InlineKeyboardButton, InlineKeyboardMarkup

def leaderboard_buttons(active="today"):
    modes = [("Today","today"), ("Week","week"), ("Month","month"), ("All","all")]
    row = [InlineKeyboardButton(text=(f"✅ {label}" if mode==active else label), callback_data=mode) for label,mode in modes]
    # return InlineKeyboardMarkup as single row
    return InlineKeyboardMarkup([row])
