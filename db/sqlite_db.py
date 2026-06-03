"""PostgreSQL database — Supabase hosted. Replaces sqlite_db.py."""
import os
import logging
import psycopg2
import psycopg2.extras

log = logging.getLogger("postgres_db")

# Connection string — set via env var or .streamlit/secrets.toml loader below
def _get_dsn() -> str:
    # 1. Explicit env var
    dsn = os.environ.get("SUPABASE_DSN")
    if dsn:
        return dsn
    # 2. Streamlit secrets (when running in Streamlit)
    try:
        import streamlit as st
        return st.secrets["supabase"]["dsn"]
    except Exception:
        pass
    # 3. Local secrets.toml fallback
    try:
        from pathlib import Path
        import tomllib
        p = Path(__file__).parent.parent / ".streamlit" / "secrets.toml"
        with open(p, "rb") as f:
            s = tomllib.load(f)
        return s["supabase"]["dsn"]
    except Exception:
        pass
    raise RuntimeError("No SUPABASE_DSN found. Set env var or .streamlit/secrets.toml")


def get_connection(path: str | None = None):
    """Return a psycopg2 connection with RealDictCursor as row factory."""
    dsn = _get_dsn()
    conn = psycopg2.connect(dsn, cursor_factory=psycopg2.extras.RealDictCursor, sslmode="require")
    conn.autocommit = False
    return conn


def init_schema(conn) -> None:
    """Create all tables if they don't exist. Safe to re-run."""
    cur = conn.cursor()
    cur.execute("""
    CREATE TABLE IF NOT EXISTS competitors (
        id SERIAL PRIMARY KEY,
        handle TEXT NOT NULL,
        platform TEXT NOT NULL,
        category TEXT,
        enabled INTEGER DEFAULT 1,
        added_at TIMESTAMP DEFAULT NOW(),
        UNIQUE(handle, platform)
    );
    CREATE TABLE IF NOT EXISTS competitor_posts (
        id SERIAL PRIMARY KEY,
        competitor_id INTEGER REFERENCES competitors(id),
        post_url TEXT UNIQUE NOT NULL,
        caption TEXT,
        thumbnail_url TEXT,
        ai_analysis TEXT,
        views INTEGER,
        likes INTEGER,
        comments INTEGER,
        saves INTEGER,
        posted_at TIMESTAMP,
        scraped_at TIMESTAMP DEFAULT NOW()
    );
    CREATE TABLE IF NOT EXISTS trends (
        id SERIAL PRIMARY KEY,
        source TEXT,
        topic TEXT NOT NULL,
        signal_strength REAL,
        raw_data TEXT,
        detected_at TIMESTAMP DEFAULT NOW()
    );
    CREATE TABLE IF NOT EXISTS reddit_posts (
        id SERIAL PRIMARY KEY,
        subreddit TEXT NOT NULL,
        reddit_id TEXT UNIQUE NOT NULL,
        title TEXT,
        body TEXT,
        upvotes INTEGER,
        num_comments INTEGER,
        url TEXT,
        posted_at TIMESTAMP,
        scraped_at TIMESTAMP DEFAULT NOW()
    );
    CREATE TABLE IF NOT EXISTS saved_post_analysis (
        id SERIAL PRIMARY KEY,
        post_url TEXT UNIQUE NOT NULL,
        collection TEXT NOT NULL,
        hook_text TEXT,
        hook_type TEXT,
        format_notes TEXT,
        caption_style TEXT,
        visual_pattern TEXT,
        raw_insight TEXT,
        analyzed_at TIMESTAMP DEFAULT NOW()
    );
    CREATE TABLE IF NOT EXISTS comments (
        id SERIAL PRIMARY KEY,
        post_url TEXT,
        source TEXT,
        platform TEXT,
        body TEXT NOT NULL,
        sentiment TEXT,
        category TEXT,
        scraped_at TIMESTAMP DEFAULT NOW(),
        analyzed_at TIMESTAMP
    );
    CREATE TABLE IF NOT EXISTS comment_insights (
        id SERIAL PRIMARY KEY,
        category TEXT NOT NULL,
        insight TEXT NOT NULL,
        frequency INTEGER DEFAULT 1,
        example_comment TEXT,
        generated_at TIMESTAMP DEFAULT NOW()
    );
    CREATE TABLE IF NOT EXISTS scripts (
        id SERIAL PRIMARY KEY,
        pain_point TEXT NOT NULL,
        source_subreddit TEXT,
        hook TEXT NOT NULL,
        problem TEXT NOT NULL,
        insight TEXT NOT NULL,
        cta TEXT NOT NULL,
        format TEXT DEFAULT 'talking_head',
        generated_at TIMESTAMP DEFAULT NOW()
    );
    CREATE TABLE IF NOT EXISTS reports (
        id SERIAL PRIMARY KEY,
        type TEXT NOT NULL,
        period_start TIMESTAMP,
        period_end TIMESTAMP,
        body_md TEXT,
        sent_via_telegram INTEGER DEFAULT 0,
        created_at TIMESTAMP DEFAULT NOW()
    );
    CREATE TABLE IF NOT EXISTS daily_briefs (
        id SERIAL PRIMARY KEY,
        body_md TEXT,
        generated_by TEXT DEFAULT 'Dwight',
        created_at TIMESTAMP DEFAULT NOW()
    );
    CREATE TABLE IF NOT EXISTS opportunities (
        id SERIAL PRIMARY KEY,
        type TEXT,
        title TEXT NOT NULL,
        score INTEGER DEFAULT 0,
        notes TEXT,
        source_url TEXT,
        alerted_at TIMESTAMP,
        status TEXT DEFAULT 'new',
        created_at TIMESTAMP DEFAULT NOW()
    );
    CREATE TABLE IF NOT EXISTS employees (
        id SERIAL PRIMARY KEY,
        name TEXT UNIQUE NOT NULL,
        type TEXT NOT NULL,
        enabled INTEGER DEFAULT 1,
        last_run_at TIMESTAMP,
        last_status TEXT
    );
    CREATE TABLE IF NOT EXISTS hook_performance (
        id SERIAL PRIMARY KEY,
        hook_text TEXT NOT NULL,
        date_posted DATE,
        platform TEXT,
        post_url TEXT,
        views INTEGER DEFAULT 0,
        reach INTEGER DEFAULT 0,
        shares INTEGER DEFAULT 0,
        saves INTEGER DEFAULT 0,
        comments INTEGER DEFAULT 0,
        likes INTEGER DEFAULT 0,
        followers_gained INTEGER DEFAULT 0,
        engagement_rate REAL DEFAULT 0.0,
        view_velocity REAL DEFAULT 0.0,
        recorded_at TIMESTAMP DEFAULT NOW()
    );
    CREATE TABLE IF NOT EXISTS swipe_file (
        id SERIAL PRIMARY KEY,
        source_url TEXT UNIQUE NOT NULL,
        platform TEXT,
        collection TEXT,
        hook_text TEXT,
        topic TEXT,
        creator_handle TEXT,
        content_format TEXT,
        emotional_trigger TEXT,
        narrative_style TEXT,
        date_saved TIMESTAMP DEFAULT NOW(),
        personal_rating INTEGER DEFAULT 0,
        notes TEXT,
        analyzed INTEGER DEFAULT 0,
        chroma_id TEXT
    );
    CREATE TABLE IF NOT EXISTS opinion_topics (
        id SERIAL PRIMARY KEY,
        topic TEXT NOT NULL,
        type TEXT DEFAULT 'question',
        source TEXT,
        relevance_score REAL DEFAULT 0.0,
        generated_at TIMESTAMP DEFAULT NOW(),
        used INTEGER DEFAULT 0
    );
    CREATE TABLE IF NOT EXISTS upload_queue (
        id SERIAL PRIMARY KEY,
        file_path TEXT NOT NULL,
        metadata_path TEXT,
        platform TEXT DEFAULT 'youtube',
        title TEXT,
        description TEXT,
        tags TEXT,
        publish_at TIMESTAMP,
        status TEXT DEFAULT 'pending',
        uploaded_at TIMESTAMP,
        youtube_id TEXT,
        error_msg TEXT,
        created_at TIMESTAMP DEFAULT NOW()
    );
    CREATE TABLE IF NOT EXISTS employee_activity_log (
        id SERIAL PRIMARY KEY,
        employee TEXT NOT NULL,
        action TEXT NOT NULL,
        detail TEXT,
        logged_at TIMESTAMP DEFAULT NOW()
    );
    """)
    conn.commit()
    cur.close()


def seed_competitors(conn, handles: list, platform: str) -> None:
    cur = conn.cursor()
    cur.executemany(
        "INSERT INTO competitors (handle, platform) VALUES (%s, %s) ON CONFLICT DO NOTHING",
        [(h, platform) for h in handles]
    )
    conn.commit()
    cur.close()


def seed_employees(conn, employees: dict) -> None:
    cur = conn.cursor()
    for name, cfg in employees.items():
        cur.execute(
            "INSERT INTO employees (name, type, enabled) VALUES (%s, %s, %s) ON CONFLICT DO NOTHING",
            (name, cfg["type"], 1 if cfg.get("enabled", True) else 0)
        )
    conn.commit()
    cur.close()


def update_employee_status(conn, name: str, status: str) -> None:
    cur = conn.cursor()
    cur.execute(
        "UPDATE employees SET last_run_at=NOW(), last_status=%s WHERE name=%s",
        (status, name)
    )
    conn.commit()
    cur.close()
