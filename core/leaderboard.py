import io
from PIL import Image, ImageDraw, ImageFont
from utils.db import get_top_users
from utils.image_theme import get_theme


async def generate_leaderboard_image():
    """
    Generate leaderboard image from top user data in DB.
    """

    # Get leaderboard data
    top_users = await get_top_users(limit=10)
    theme = get_theme()

    # Canvas setup
    width, height = 800, 600
    background_color = theme["background_color"]
    text_color = theme["text_color"]
    accent_color = theme["accent_color"]

    image = Image.new("RGB", (width, height), background_color)
    draw = ImageDraw.Draw(image)

    # Title
    title_font = ImageFont.truetype(theme["font_path"], 40)
    draw.text((width / 2 - 180, 30), "🏆 Leaderboard 🏆", fill=accent_color, font=title_font)

    # Font for list
    font = ImageFont.truetype(theme["font_path"], 28)
    y = 120

    if not top_users:
        draw.text((200, 250), "No players yet!", fill=text_color, font=font)
    else:
        for i, user in enumerate(top_users, start=1):
            name = user.get("username", f"User {i}")
            points = user.get("points", 0)
            draw.text((100, y), f"{i}. {name}", fill=text_color, font=font)
            draw.text((600, y), f"{points} pts", fill=accent_color, font=font)
            y += 45

    # Save to buffer
    output = io.BytesIO()
    image.save(output, format="PNG")
    output.seek(0)
    return output
