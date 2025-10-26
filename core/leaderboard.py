# =========================================
# 📂 core/leaderboard.py
# =========================================
import io
from PIL import Image, ImageDraw, ImageFont
import matplotlib
import random
from pymongo import DESCENDING
from utils.db import db  # ✅ use db instance (not messages_collection)
from utils.image_theme import get_theme_colors

# ✅ Font fix for Heroku (emoji / symbol support)
matplotlib.rcParams['font.family'] = 'DejaVu Sans'

# =========================================
# Get leaderboard data from MongoDB
# =========================================
def get_leaderboard_data(limit=10):
    messages_collection = db["messages"]  # dynamically get collection
    top_users = list(messages_collection.find().sort("count", DESCENDING).limit(limit))
    return top_users


# =========================================
# Create leaderboard image dynamically
# =========================================
def create_leaderboard_image(top_users, theme="default"):
    """Generate leaderboard image dynamically."""
    theme_colors = get_theme_colors(theme)

    width, height = 800, 600
    bg_color = theme_colors["background"]
    text_color = theme_colors["text"]
    accent_color = theme_colors["accent"]

    # Create base image
    img = Image.new("RGB", (width, height), color=bg_color)
    draw = ImageDraw.Draw(img)

    # Title
    title_font = ImageFont.truetype("arial.ttf", 40)
    text_font = ImageFont.truetype("arial.ttf", 28)
    small_font = ImageFont.truetype("arial.ttf", 22)

    title = "🏆 ChatFight Leaderboard"
    tw, th = draw.textsize(title, font=title_font)
    draw.text(((width - tw) / 2, 30), title, fill=accent_color, font=title_font)

    # If no users
    if not top_users:
        draw.text((width / 2 - 100, height / 2), "No data yet 😔", fill=text_color, font=text_font)
        bio = io.BytesIO()
        img.save(bio, format="PNG")
        bio.seek(0)
        return bio

    # Draw each user
    start_y = 120
    spacing = 40
    medals = ["🥇", "🥈", "🥉"]

    for i, user in enumerate(top_users):
        username = user.get("username", "Anonymous")
        count = user.get("count", 0)

        medal = medals[i] if i < len(medals) else f"#{i+1}"
        color = accent_color if i < 3 else text_color

        y = start_y + i * spacing
        rank_text = f"{medal} {username} — {count} msgs"
        draw.text((100, y), rank_text, fill=color, font=text_font)

    # Footer
    footer = "✨ Powered by STD-DEEPANSHU Bot"
    fw, fh = draw.textsize(footer, font=small_font)
    draw.text((width - fw - 20, height - fh - 20), footer, fill=text_color, font=small_font)

    # Convert to byte stream
    bio = io.BytesIO()
    img.save(bio, format="PNG")
    bio.seek(0)
    return bio
