from telegram import InlineKeyboardButton, InlineKeyboardMarkup

def leaderboard_buttons(current_view):
    buttons = [
        [
            InlineKeyboardButton(f"Overall {'✅' if current_view == 'all' else ''}", callback_data='view_all'),
            InlineKeyboardButton(f"Today {'✅' if current_view == 'today' else ''}", callback_data='view_today'),
        ],
        [
            InlineKeyboardButton(f"Week {'✅' if current_view == 'week' else ''}", callback_data='view_week'),
            InlineKeyboardButton(f"Month {'✅' if current_view == 'month' else ''}", callback_data='view_month'),
        ]
    ]
    return InlineKeyboardMarkup(buttons)
