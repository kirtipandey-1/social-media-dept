"""Cached database query helpers for all dashboard pages."""
import streamlit as st
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from db.sqlite_db import get_connection
from db.duckdb_db import get_connection as dq_conn


@st.cache_data(ttl=300)
def get_recent_trends(limit=20):
    conn = get_connection()
    rows = conn.execute("""
    SELECT topic, source, signal_strength, detected_at
    FROM trends ORDER BY detected_at DESC LIMIT ?
    """, (limit,)).fetchall()
    return [dict(r) for r in rows]

@st.cache_data(ttl=300)
def get_competitor_posts(limit=30):
    conn = get_connection()
    rows = conn.execute("""
    SELECT c.handle, cp.post_url, cp.caption, cp.views, cp.likes, cp.scraped_at
    FROM competitor_posts cp JOIN competitors c ON cp.competitor_id=c.id
    ORDER BY cp.scraped_at DESC LIMIT ?
    """, (limit,)).fetchall()
    return [dict(r) for r in rows]

@st.cache_data(ttl=300)
def get_top_opportunities(limit=10):
    conn = get_connection()
    rows = conn.execute("""
    SELECT title, score, type, notes, status
    FROM opportunities WHERE status='new' ORDER BY score DESC LIMIT ?
    """, (limit,)).fetchall()
    return [dict(r) for r in rows]

@st.cache_data(ttl=300)
def get_recent_reddit(limit=20):
    conn = get_connection()
    rows = conn.execute("""
    SELECT title, subreddit, upvotes, url, posted_at
    FROM reddit_posts ORDER BY posted_at DESC LIMIT ?
    """, (limit,)).fetchall()
    return [dict(r) for r in rows]

@st.cache_data(ttl=60)
def get_latest_report(report_type="daily"):
    conn = get_connection()
    row = conn.execute("""
    SELECT body_md, created_at FROM reports WHERE type=?
    ORDER BY created_at DESC LIMIT 1
    """, (report_type,)).fetchone()
    return dict(row) if row else None

@st.cache_data(ttl=60)
def get_latest_daily_brief():
    conn = get_connection()
    row = conn.execute("""
    SELECT body_md, created_at FROM daily_briefs
    ORDER BY created_at DESC LIMIT 1
    """).fetchone()
    return dict(row) if row else None

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

def get_scripts(limit=20):
    conn = get_connection()
    rows = conn.execute("""
    SELECT id, pain_point, hook, problem, insight, cta, generated_at
    FROM scripts ORDER BY generated_at DESC LIMIT ?
    """, (limit,)).fetchall()
    return [dict(r) for r in rows]

def get_pain_points_from_insights(limit=10):
    conn = get_connection()
    rows = conn.execute("""
    SELECT insight, frequency, example_comment, category
    FROM comment_insights ORDER BY frequency DESC LIMIT ?
    """, (limit,)).fetchall()
    return [dict(r) for r in rows]

def get_swipe_file(limit=20):
    conn = get_connection()
    rows = conn.execute("""
    SELECT source_url, platform, hook_text, topic, creator_handle, content_format,
           emotional_trigger, personal_rating, date_saved, notes
    FROM swipe_file ORDER BY date_saved DESC LIMIT ?
    """, (limit,)).fetchall()
    return [dict(r) for r in rows]

def get_opinion_topics(limit=20):
    conn = get_connection()
    rows = conn.execute("""
    SELECT topic, type, source, relevance_score, generated_at
    FROM opinion_topics ORDER BY relevance_score DESC, generated_at DESC LIMIT ?
    """, (limit,)).fetchall()
    return [dict(r) for r in rows]

def get_employee_activity(limit=30):
    conn = get_connection()
    rows = conn.execute("""
    SELECT employee, action, detail, logged_at
    FROM employee_activity_log ORDER BY logged_at DESC LIMIT ?
    """, (limit,)).fetchall()
    return [dict(r) for r in rows]
