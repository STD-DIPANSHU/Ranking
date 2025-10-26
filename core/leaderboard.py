# =========================================
# 📂 core/leaderboard.py
# =========================================

import matplotlib.pyplot as plt
from datetime import datetime, timedelta
from io import BytesIO
import os

from utils.db import get_leaderboard_from_db
from utils.image_theme import get_theme_colors


# =========================================
# 🧠 FETCH DATA
# =========================================
def get_leaderboard_data(mode: str):
    """
    mode: today / week / month / all
    """
    now = datetime.utcnow()

    if mode == "today":
        start_date = now.strftime("%Y-%m-%d")
        query = {"date": start_date}
    elif mode == "week":
        start_date = (now - timedelta(days=7)).strftime("%Y-%m-%d")
        query = {"date": {"$gte": start_date}}
    elif mode == "month":
        start_date = (now - timedelta(days=30)).strftime("%Y-%m-%d")
        query = {"date": {"$gte": start_date}}
    else:
        query = {}

    return get_leaderboard_from_db(query)


# =========================================
# 🎨 IMAGE CREATOR
# =========================================
def create_leaderboard_image(rows, mode="all"):
    colors = get_theme_colors()
    names = [r["username"] for r in rows][::-1]
    counts = [r["count"] for r in rows][::-1]
    total_users = len(names)

    fig, ax = plt.subplots(figsize=(9, max(3, 0.6 * total_users)))
    fig.patch.set_facecolor(colors["bg"])
    ax.set_facecolor(colors["bg"])

    bars = ax.barh(
        range(total_users),
        counts,
        color=colors["bar"],
        edgecolor=colors["bar_edge"],
        linewidth=1.5,
    )

    ax.set_yticks(range(total_users))
    ax.set_yticklabels(names, fontsize=11, color=colors["text"], fontweight="bold")
    ax.set_xlabel("Messages", color=colors["text"])
    ax.set_title(
        f"🏆 ChatFight {mode.title()} Leaderboard 🏆",
        color=colors["title"],
        fontsize=15,
        fontweight="bold",
        pad=15,
    )

    for bar, val in zip(bars, counts):
        ax.text(
            bar.get_width() + 1,
            bar.get_y() + bar.get_height() / 2,
            f"{val}",
            va="center",
            ha="left",
            color=colors["accent"],
            fontsize=10,
            fontweight="bold",
        )

    for spine in ax.spines.values():
        spine.set_visible(False)

    ax.grid(axis="x", color=colors["grid"], linestyle="--", alpha=0.3)
    plt.tight_layout()

    img_path = f"/tmp/leaderboard_{mode}.png"
    plt.savefig(img_path, bbox_inches="tight", dpi=150, facecolor=fig.get_facecolor())
    plt.close()
    return img_path
