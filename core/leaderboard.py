# core/leaderboard.py
import io
import matplotlib
matplotlib.rcParams['font.family'] = 'DejaVu Sans'  # safer default on Heroku for many glyphs
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
from utils.db import get_leaderboard_from_db

def get_leaderboard_data(chat_id: int, mode: str):
    now = datetime.utcnow()
    if mode == "today":
        query = {"chat_id": chat_id, "date": now.strftime("%Y-%m-%d")}
        title = "Today's Leaderboard"
    elif mode == "week":
        start = (now - timedelta(days=7)).strftime("%Y-%m-%d")
        query = {"chat_id": chat_id, "date": {"$gte": start}}
        title = "This Week's Leaderboard"
    elif mode == "month":
        start = (now - timedelta(days=30)).strftime("%Y-%m-%d")
        query = {"chat_id": chat_id, "date": {"$gte": start}}
        title = "This Month's Leaderboard"
    else:
        query = {"chat_id": chat_id}
        title = "All-Time Leaderboard"

    rows = get_leaderboard_from_db(query)
    return rows, title

def create_leaderboard_image(rows, title="Leaderboard"):
    # rows: list of {"username": ..., "count": ...} (top first)
    if not rows:
        # simple placeholder image
        fig, ax = plt.subplots(figsize=(6,2))
        ax.axis('off')
        ax.text(0.5, 0.5, "No data yet", ha='center', va='center', fontsize=16, color='white')
        fig.patch.set_facecolor('#0d0000')
        ax.set_facecolor('#0d0000')
        buf = io.BytesIO()
        plt.savefig(buf, format='png', bbox_inches='tight', facecolor=fig.get_facecolor(), dpi=150)
        plt.close(fig)
        buf.seek(0)
        return buf

    names = [r["username"] for r in rows][::-1]   # reverse for horizontal bar order
    counts = [r["count"] for r in rows][::-1]

    fig, ax = plt.subplots(figsize=(8, max(3, 0.6 * len(names))))
    fig.patch.set_facecolor('#0d0000')
    ax.set_facecolor('#0d0000')

    bars = ax.barh(range(len(names)), counts, color='#b30000', edgecolor='#ff3333', linewidth=1.2)
    ax.set_yticks(range(len(names)))
    ax.set_yticklabels(names, color='white', fontsize=11)
    ax.invert_yaxis()
    ax.set_xlabel('Messages', color='white')
    ax.set_title(title, color='#ff6666', fontsize=14, pad=10)

    for bar, val in zip(bars, counts):
        ax.text(bar.get_width() + max(1, val*0.01), bar.get_y() + bar.get_height()/2,
                f"{val}", va='center', color='#ffcccc', fontsize=10)

    for spine in ax.spines.values():
        spine.set_visible(False)

    ax.grid(axis='x', color='#331111', linestyle='--', alpha=0.3)
    plt.tight_layout()

    buf = io.BytesIO()
    plt.savefig(buf, format='png', bbox_inches='tight', facecolor=fig.get_facecolor(), dpi=150)
    plt.close(fig)
    buf.seek(0)
    return buf
