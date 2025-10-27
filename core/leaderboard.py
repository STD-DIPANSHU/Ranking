import datetime
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO
from utils.db import get_top_users
from utils.image_theme import get_theme


async def generate_leaderboard_image(scope: str, chat_id: int):
    """Create leaderboard image from DB stats"""
    data = await get_top_users(chat_id, scope)
    if not data:
        return None

    width, height = 800, 400
    img = Image.new("RGB", (width, height), color=(25, 25, 30))
    draw = ImageDraw.Draw(img)
    font = ImageFont.truetype("arial.ttf", 28)

    draw.text((20, 20), f"LEADERBOARD ({scope.upper()})", fill=(255, 255, 255), font=font)

    y = 80
    for i, user in enumerate(data, start=1):
        name = user.get("name", "Unknown")[:20]
        count = user.get("count", 0)
        draw.text((50, y), f"{i}. {name}", fill=(180, 200, 255), font=font)
        draw.text((600, y), f"{count}", fill=(255, 255, 255), font=font)
        y += 40

    output = BytesIO()
    img.save(output, format="PNG")
    output.seek(0)
    return output
