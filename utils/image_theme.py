# =========================================
# 📂 utils/image_theme.py
# =========================================

def get_theme_colors(theme="default"):
    """
    Return color scheme for leaderboard image.
    Future: Can add more themes here easily.
    """

    themes = {
        "default": {
            "background": (15, 15, 30),
            "text": (255, 255, 255),
            "accent": (255, 215, 0),
        },
        "cyberpunk": {
            "background": (10, 10, 20),
            "text": (0, 255, 255),
            "accent": (255, 0, 255),
        },
        "pastel": {
            "background": (240, 235, 255),
            "text": (60, 60, 80),
            "accent": (140, 120, 255),
        },
        "darkred": {
            "background": (40, 0, 0),
            "text": (255, 230, 230),
            "accent": (255, 50, 50),
        },
    }

    return themes.get(theme, themes["default"])
