"""Cached database query helpers for all dashboard pages."""
import streamlit as st
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from db.sqlite_db import get_connection
from db.duckdb_db import get_connection as dq_conn


def _safe_query(fn):
    """Decorator: return [] on any DB error (missing table, empty DB, etc)."""
    import functools
    @functools.wraps(fn)
    def wrapper(*args, **kwargs):
        try:
            return fn(*args, **kwargs)
        except Exception:
            return []
    return wrapper


@st.cache_data(ttl=300)
@_safe_query
def get_recent_trends(limit=20):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
    SELECT topic, source, signal_strength, detected_at
    FROM trends ORDER BY detected_at DESC LIMIT %s
    """, (limit,))
    return [dict(r) for r in cur.fetchall()]

@st.cache_data(ttl=300)
@_safe_query
def get_competitor_posts(limit=30):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
    SELECT c.handle, cp.post_url, cp.caption, cp.views, cp.likes,
           cp.thumbnail_url, cp.ai_analysis, cp.scraped_at
    FROM competitor_posts cp JOIN competitors c ON cp.competitor_id=c.id
    ORDER BY cp.views DESC, cp.scraped_at DESC LIMIT %s
    """, (limit,))
    return [dict(r) for r in cur.fetchall()]

@st.cache_data(ttl=300)
@_safe_query
def get_top_opportunities(limit=10):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
    SELECT title, score, type, notes, status
    FROM opportunities WHERE status='new' ORDER BY score DESC LIMIT %s
    """, (limit,))
    return [dict(r) for r in cur.fetchall()]

@st.cache_data(ttl=300)
@_safe_query
def get_recent_reddit(limit=20):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
    SELECT title, subreddit, upvotes, url, posted_at
    FROM reddit_posts
    ORDER BY upvotes DESC, posted_at DESC LIMIT %s
    """, (limit,))
    return [dict(r) for r in cur.fetchall()]

@st.cache_data(ttl=60)
def get_latest_report(report_type="daily"):
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("""
        SELECT body_md, created_at FROM reports WHERE type=%s
        ORDER BY created_at DESC LIMIT 1
        """, (report_type,))
        row = cur.fetchone()
        return dict(row) if row else None
    except Exception:
        return None

@st.cache_data(ttl=60)
def get_latest_daily_brief():
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("""
        SELECT body_md, created_at FROM daily_briefs
        ORDER BY created_at DESC LIMIT 1
        """)
        row = cur.fetchone()
        return dict(row) if row else None
    except Exception:
        return None

@st.cache_data(ttl=300)
def get_post_performance(limit=20):
    try:
        conn = dq_conn()
        rows = conn.execute("""
        SELECT post_url, platform, views, likes, saves, comments, posted_at
        FROM post_performance ORDER BY posted_at DESC LIMIT ?
        """, (limit,)).fetchall()
        return [{"post_url":r[0],"platform":r[1],"views":r[2],
                 "likes":r[3],"saves":r[4],"comments":r[5],"posted_at":str(r[6])}
                for r in rows]
    except Exception:
        return []

@_safe_query
def get_scripts(limit=20):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
    SELECT id, pain_point, hook, problem, insight, cta, generated_at
    FROM scripts ORDER BY generated_at DESC LIMIT %s
    """, (limit,))
    return [dict(r) for r in cur.fetchall()]

@_safe_query
def get_pain_points_from_insights(limit=10):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
    SELECT insight, frequency, example_comment, category
    FROM comment_insights ORDER BY frequency DESC LIMIT %s
    """, (limit,))
    return [dict(r) for r in cur.fetchall()]

@_safe_query
def get_swipe_file(limit=20):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
    SELECT source_url, platform, hook_text, topic, creator_handle, content_format,
           emotional_trigger, personal_rating, date_saved, notes
    FROM swipe_file ORDER BY date_saved DESC LIMIT %s
    """, (limit,))
    return [dict(r) for r in cur.fetchall()]

@_safe_query
def get_opinion_topics(limit=20):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
    SELECT topic, type, source, relevance_score, generated_at
    FROM opinion_topics ORDER BY relevance_score DESC, generated_at DESC LIMIT %s
    """, (limit,))
    return [dict(r) for r in cur.fetchall()]

@_safe_query
def get_employee_activity(limit=30):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
    SELECT employee, action, detail, logged_at
    FROM employee_activity_log ORDER BY logged_at DESC LIMIT %s
    """, (limit,))
    return [dict(r) for r in cur.fetchall()]

@st.cache_data(ttl=120)
def get_suggested_topics(limit=10) -> list:
    """Return suggested hook topics from recent Reddit + trends data."""
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("""
        SELECT topic FROM trends
        ORDER BY detected_at DESC LIMIT 20
        """)
        trend_rows = cur.fetchall()
        cur.execute("""
        SELECT title FROM reddit_posts
        WHERE scraped_at > NOW() - INTERVAL '7 days'
        ORDER BY upvotes DESC LIMIT 30
        """)
        reddit_rows = cur.fetchall()
        topics = []
        for r in trend_rows:
            t = r["topic"].strip() if r["topic"] else ""
            if t and t not in topics:
                topics.append(t)
        for r in reddit_rows:
            t = (r["title"] or "").strip()[:60]
            if t and t not in topics:
                topics.append(t)
        return topics[:limit]
    except Exception:
        return []
