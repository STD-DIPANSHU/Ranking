# ================================
# ChatFight Bot — Leaderboard Logic
# ================================
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from io import BytesIO
from datetime import datetime, timedelta
from utils.db import messages_collection, get_top_users


def get_leaderboard_data(chat_id, mode="today"):
    now = datetime.utcnow()
    if mode == "week":
        start = (now - timedelta(days=7)).strftime("%Y-%m-%d")
        query = {"chat_id": chat_id, "date": {"$gte": start}}
        title = "🔥 Weekly Leaderboard"
    elif mode == "month":
        start = (now - timedelta(days=30)).strftime("%Y-%m-%d")
        query = {"chat_id": chat_id, "date": {"$gte": start}}
        title = "🌙 Monthly Leaderboard"
    elif mode == "all":
        query = {"chat_id": chat_id}
        title = "🏆 All-Time Leaderboard"
    else:
        today = now.strftime("%Y-%m-%d")
        query = {"chat_id": chat_id, "date": today}
        title = "⚡ Today's Leaderboard"

    data = list(messages_collection.aggregate([
        {"$match": query},
        {"$group": {"_id": "$username", "total": {"$sum": "$count"}}},
        {"$sort": {"total": -1}},
        {"$limit": 10}
    ]))
    rows = [{"username": d["_id"], "total": d["total"]} for d in data]
    return rows, title


def create_leaderboard_image(rows, title="Leaderboard"):
    names = [r["username"] for r in rows][::-1]
    counts = [r["total"] for r in rows][::-1]
    total_users = len(names)

    plt.figure(figsize=(9, max(3, 0.7 * total_users)))
    ax = plt.gca()
    ax.set_facecolor("#0d0000")
    fig = plt.gcf()
    fig.patch.set_facecolor("#0d0000")

    bars = plt.barh(range(total_users), counts, color="#b30000", edgecolor="#ff3333", linewidth=1.5)
    plt.yticks(range(total_users), names, fontsize=12, color="white", fontweight="bold")
    plt.xlabel("Messages", color="white", fontsize=12)
    plt.title(title, color="#ff6666", fontsize=16, fontweight="bold", pad=15)

    for bar, val in zip(bars, counts):
        ax.text(bar.get_width() + 1, bar.get_y() + bar.get_height() / 2, str(val),
                va="center", ha="left", color="#ffcccc", fontsize=11, fontweight="bold")

    for bar in bars:
        rect = patches.Rectangle((0, bar.get_y()), bar.get_width(), bar.get_height(),
                                 linewidth=0, facecolor="#ff0000", alpha=0.05)
        ax.add_patch(rect)

    plt.grid(axis="x", color="#331111", linestyle="--", alpha=0.3)
    plt.tight_layout()

    bio = BytesIO()
    plt.savefig(bio, format="png", dpi=150, bbox_inches="tight", facecolor=fig.get_facecolor())
    plt.close()
    bio.seek(0)
    return bio
