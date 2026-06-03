#!/usr/bin/env python3
"""Telegram bot — handles /employee slash commands for daily briefs.
Run standalone: .venv/bin/python workers/telegram_bot.py
Kept alive by launchd: com.socialdept.telegram
"""
import sys
import logging
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from config import load_settings

log = logging.getLogger("telegram_bot")
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(name)s] %(levelname)s: %(message)s")


def _allowed(update: Update) -> bool:
    s = load_settings()
    return str(update.effective_chat.id) == str(s.get("telegram", {}).get("chat_id", ""))


def _db_brief(employee_name: str) -> str:
    from db.sqlite_db import get_connection
    conn = get_connection()
    rows = conn.execute("""
    SELECT action, detail, logged_at FROM employee_activity_log
    WHERE employee=? ORDER BY logged_at DESC LIMIT 5
    """, (employee_name,)).fetchall()
    if not rows:
        return f"*{employee_name}* has no activity logged yet."
    lines = [f"*{employee_name} — Recent Activity*\n"]
    for r in rows:
        lines.append(f"• {r['action']}: {r['detail'] or ''} _{r['logged_at']}_")
    return "\n".join(lines)


def _research_brief() -> str:
    from db.sqlite_db import get_connection
    conn = get_connection()
    reddit = conn.execute("""
    SELECT title, subreddit, upvotes FROM reddit_posts
    ORDER BY upvotes DESC, scraped_at DESC LIMIT 5
    """).fetchall()
    comp = conn.execute("""
    SELECT c.handle, cp.views FROM competitor_posts cp
    JOIN competitors c ON cp.competitor_id=c.id
    ORDER BY cp.views DESC LIMIT 3
    """).fetchall()
    lines = ["*Chad — Research Brief* 💪\n"]
    if reddit:
        lines.append("*Top Reddit Posts:*")
        for r in reddit:
            lines.append(f"• r/{r['subreddit']}: {r['title'][:60]} ({r['upvotes']} upvotes)")
    if comp:
        lines.append("\n*Top Competitor Posts:*")
        for c in comp:
            lines.append(f"• @{c['handle']}: {c['views'] or 0:,} views")
    return "\n".join(lines) or "Chad has no data yet."


def _hooks_brief() -> str:
    try:
        from db.chroma_db import get_collection
        col = get_collection()
        count = col.count()
        results = col.get(include=["documents"])
        docs = (results.get("documents") or [])[:5]
        lines = [f"*Peter — Hooks Brief* 🎣\n{count} hooks in database.\n*Top 5:*"]
        for h in docs:
            lines.append(f"• {h}")
        return "\n".join(lines) if docs else f"Peter has {count} hooks stored. Generate more on the dashboard."
    except Exception as e:
        return f"Peter: error fetching hooks — {e}"


def _report_brief() -> str:
    from db.sqlite_db import get_connection
    conn = get_connection()
    row = conn.execute("""
    SELECT body_md, created_at FROM reports WHERE type='daily'
    ORDER BY created_at DESC LIMIT 1
    """).fetchone()
    if row:
        return f"*McLovin — Daily Report* 🤓\n_{row['created_at']}_\n\n{row['body_md'][:1000]}"
    return "McLovin has no reports yet. Run the pipeline first."


def _borat_brief() -> str:
    from db.sqlite_db import get_connection
    conn = get_connection()
    opps = conn.execute("""
    SELECT title, score FROM opportunities WHERE status='new'
    ORDER BY score DESC LIMIT 5
    """).fetchall()
    lines = ["*Borat — Opportunities* 🎉 VERY NICE!\n"]
    if opps:
        for o in opps:
            lines.append(f"• {o['title']} (score: {o['score']})")
    else:
        lines.append("No new opportunities. Very sad!")
    return "\n".join(lines)


def _strategy_brief() -> str:
    from db.sqlite_db import get_connection
    conn = get_connection()
    row = conn.execute("""
    SELECT body_md, created_at FROM reports WHERE type='daily'
    ORDER BY created_at DESC LIMIT 1
    """).fetchone()
    brief = row["body_md"][:800] if row else "No daily brief yet."
    return f"*Dwight — Strategy Brief* 📋\nACTION REQUIRED:\n\n{brief}"


EMPLOYEE_HANDLERS = {
    "chad":    ("Chad",    _research_brief),
    "peter":   ("Peter",   _hooks_brief),
    "mclovin": ("McLovin", _report_brief),
    "karen":   ("Karen",   lambda: _db_brief("Karen")),
    "borat":   ("Borat",   _borat_brief),
    "dwight":  ("Dwight",  _strategy_brief),
    "rick":    ("Rick",    lambda: _db_brief("Rick")),
    "speed":   ("Speed",   lambda: _db_brief("Speed")),
    "gollum":  ("Gollum",  lambda: _db_brief("Gollum")),
    "keanu":   ("Keanu",   lambda: _db_brief("Keanu")),
    "drake":   ("Drake",   lambda: _db_brief("Drake")),
    "gandalf": ("Gandalf", lambda: _db_brief("Gandalf")),
}


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not _allowed(update):
        return
    msg = (
        "*Social Media Dept* 🎵\n\n"
        "Employee commands:\n" +
        "\n".join(f"/{k} — {v[0]}" for k, v in EMPLOYEE_HANDLERS.items()) +
        "\n\n/status — Pipeline status"
    )
    await update.message.reply_text(msg, parse_mode="Markdown")


async def status(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not _allowed(update):
        return
    from db.sqlite_db import get_connection
    conn = get_connection()
    reddit_count = conn.execute("SELECT COUNT(*) FROM reddit_posts").fetchone()[0]
    comp_count = conn.execute("SELECT COUNT(*) FROM competitor_posts").fetchone()[0]
    comments_count = conn.execute("SELECT COUNT(*) FROM comments").fetchone()[0]
    await update.message.reply_text(
        f"*System Status* ✅\n\nReddit posts: {reddit_count}\nCompetitor posts: {comp_count}\nComments: {comments_count}",
        parse_mode="Markdown"
    )


def _make_handler(key: str):
    async def handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        if not _allowed(update):
            return
        name, fn = EMPLOYEE_HANDLERS[key]
        await update.message.reply_text(f"_Checking in with {name}..._", parse_mode="Markdown")
        try:
            brief = fn()
        except Exception as e:
            brief = f"Error getting {name}'s brief: {e}"
        await update.message.reply_text(brief[:4096], parse_mode="Markdown")
    handler.__name__ = f"handler_{key}"
    return handler


def main():
    s = load_settings()
    token = s.get("telegram", {}).get("bot_token", "")
    if not token:
        log.error("No bot token in settings.toml [telegram] bot_token")
        sys.exit(1)
    app = ApplicationBuilder().token(token).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("status", status))
    for key in EMPLOYEE_HANDLERS:
        app.add_handler(CommandHandler(key, _make_handler(key)))
    log.info("Telegram bot polling — %d employee commands registered", len(EMPLOYEE_HANDLERS))
    app.run_polling()


if __name__ == "__main__":
    main()
