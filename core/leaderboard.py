import matplotlib.pyplot as plt
import matplotlib.patches as patches
from io import BytesIO
from datetime import datetime, timedelta
from utils.db import messages
from utils.image_theme import THEME

def get_leaderboard_data(chat_id, mode):
    now = datetime.utcnow()
    if mode == "week":
        start_date = now - timedelta(days=7)
        query = {"chat_id": chat_id, "date": {"$gte": start_date.strftime("%Y-%m-%d")}}
        title = "This Week's Leaderboard"
    elif mode == "month":
        start_date = now - timedelta(days=30)
        query = {"chat_id": chat_id, "date": {"$gte": start_date.strftime("%Y-%m-%d")}}
        title = "This Month's Leaderboard"
    elif mode == "all":
        query = {"chat_id": chat_id}
        title = "All-Time Leaderboard"
    else:
        today = now.strftime("%Y-%m-%d")
        query = {"chat_id": chat_id, "date": today}
        title = "Today's Leaderboard"

    data = list(messages.aggregate([
        {"$match": query},
        {"$group": {"_id": "$username", "total": {"$sum": "$count"}}},
        {"$sort": {"total": -1}},
        {"$limit": 10},
    ]))

    rows = [{"username": d["_id"], "total": d["total"]} for d in data]
    return rows, title


def create_leaderboard_image(rows, title="Leaderboard"):
    from matplotlib import pyplot as plt
    names = [r.get("username", "User") for r in rows][::-1]
    counts = [r.get("total", 0) for r in rows][::-1]
    total_users = len(names)

    plt.figure(figsize=(9, max(3, 0.7 * total_users)))
    ax = plt.gca()
    ax.set_facecolor(THEME["background"])
    fig = plt.gcf()
    fig.patch.set_facecolor(THEME["background"])

    bars = plt.barh(
        range(total_users),
        counts,
        color=THEME["bar_color"],
        edgecolor=THEME["edge_color"],
        linewidth=1.5,
    )

    plt.yticks(range(total_users), names, fontsize=12, color=THEME["text_color"], fontweight="bold")
    plt.xlabel("Messages", color=THEME["text_color"], fontsize=12)
    plt.title(f"🏆 {title} 🏆", color=THEME["title_color"], fontsize=16, fontweight="bold", pad=15)

    for spine in ax.spines.values():
        spine.set_visible(False)
    plt.grid(axis="x", color="#331111", linestyle="--", alpha=0.3)
    plt.tight_layout()

    bio = BytesIO()
    plt.savefig(bio, format="png", dpi=150, bbox_inches="tight", facecolor=fig.get_facecolor())
    plt.close()
    bio.seek(0)
    return bio
