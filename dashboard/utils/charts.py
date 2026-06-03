"""Visual analytics chart generator using matplotlib."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import pandas as pd


def generate_global_analytics_graphic():
    """Generate a multi-platform analytics overview chart."""
    try:
        from db.duckdb_db import get_connection
        conn = get_connection()
        rows = conn.execute("""
        SELECT platform, SUM(views) as total_views, SUM(likes) as total_likes,
               SUM(saves) as total_saves, SUM(comments) as total_comments
        FROM post_performance GROUP BY platform
        """).fetchall()
    except Exception:
        rows = []

    if not rows:
        fig, ax = plt.subplots(figsize=(10, 4))
        ax.text(0.5, 0.5, "No analytics data yet.\nSync from Instagram, YouTube, or Facebook first.",
                ha="center", va="center", fontsize=14, color="gray",
                transform=ax.transAxes)
        ax.axis("off")
        plt.tight_layout()
        return fig

    df = pd.DataFrame(rows, columns=["platform","views","likes","saves","comments"])
    fig = plt.figure(figsize=(14, 8))
    fig.suptitle("🎵 Social Media Dept — Multi-Platform Analytics", fontsize=16, fontweight="bold")
    gs = gridspec.GridSpec(2, 2, figure=fig, hspace=0.4, wspace=0.3)

    colors = {"instagram": "#C13584", "youtube": "#FF0000", "facebook": "#1877F2"}
    bar_colors = [colors.get(p.lower(), "#888888") for p in df["platform"]]

    ax1 = fig.add_subplot(gs[0, 0])
    ax1.bar(df["platform"], df["views"], color=bar_colors)
    ax1.set_title("Total Views by Platform")
    ax1.set_ylabel("Views")

    ax2 = fig.add_subplot(gs[0, 1])
    x = range(len(df))
    width = 0.25
    ax2.bar([i - width for i in x], df["likes"], width, label="Likes", color="#f59e0b")
    ax2.bar(x, df["saves"], width, label="Saves", color="#10b981")
    ax2.bar([i + width for i in x], df["comments"], width, label="Comments", color="#6366f1")
    ax2.set_xticks(list(x))
    ax2.set_xticklabels(df["platform"])
    ax2.set_title("Engagement Breakdown")
    ax2.legend()

    ax3 = fig.add_subplot(gs[1, :])
    total = df[["views","likes","saves","comments"]].sum()
    wedges, texts, autotexts = ax3.pie(
        total, labels=["Views","Likes","Saves","Comments"],
        autopct="%1.1f%%", colors=["#3b82f6","#f59e0b","#10b981","#6366f1"]
    )
    ax3.set_title("Total Engagement Distribution")

    plt.tight_layout()
    return fig
