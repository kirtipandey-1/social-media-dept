import sqlite3
from pathlib import Path

DB_PATH = Path.home() / "social-media-dept" / "db" / "social.db"

def get_connection(path: str | None = None) -> sqlite3.Connection:
    p = path or str(DB_PATH)
    Path(p).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(p)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    return conn

def init_schema(conn: sqlite3.Connection) -> None:
    conn.executescript("""
    CREATE TABLE IF NOT EXISTS competitors (
        id INTEGER PRIMARY KEY,
        handle TEXT NOT NULL,
        platform TEXT NOT NULL,
        category TEXT,
        enabled INTEGER DEFAULT 1,
        added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(handle, platform)
    );
    CREATE TABLE IF NOT EXISTS competitor_posts (
        id INTEGER PRIMARY KEY,
        competitor_id INTEGER REFERENCES competitors(id),
        post_url TEXT UNIQUE NOT NULL,
        caption TEXT,
        views INTEGER,
        likes INTEGER,
        comments INTEGER,
        saves INTEGER,
        thumbnail_url TEXT,
        ai_analysis TEXT,
        posted_at TIMESTAMP,
        scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    CREATE TABLE IF NOT EXISTS trends (
        id INTEGER PRIMARY KEY,
        source TEXT,
        topic TEXT NOT NULL,
        signal_strength REAL,
        raw_data TEXT,
        detected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    CREATE TABLE IF NOT EXISTS reddit_posts (
        id INTEGER PRIMARY KEY,
        subreddit TEXT NOT NULL,
        reddit_id TEXT UNIQUE NOT NULL,
        title TEXT,
        body TEXT,
        upvotes INTEGER,
        num_comments INTEGER,
        url TEXT,
        posted_at TIMESTAMP,
        scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    CREATE TABLE IF NOT EXISTS saved_post_analysis (
        id INTEGER PRIMARY KEY,
        post_url TEXT UNIQUE NOT NULL,
        collection TEXT NOT NULL,
        hook_text TEXT,
        hook_type TEXT,
        format_notes TEXT,
        caption_style TEXT,
        visual_pattern TEXT,
        raw_insight TEXT,
        analyzed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    CREATE TABLE IF NOT EXISTS comments (
        id INTEGER PRIMARY KEY,
        post_url TEXT,
        source TEXT,
        platform TEXT,
        body TEXT NOT NULL,
        sentiment TEXT,
        category TEXT,
        scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        analyzed_at TIMESTAMP
    );
    CREATE TABLE IF NOT EXISTS comment_insights (
        id INTEGER PRIMARY KEY,
        category TEXT NOT NULL,
        insight TEXT NOT NULL,
        frequency INTEGER DEFAULT 1,
        example_comment TEXT,
        generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    CREATE TABLE IF NOT EXISTS scripts (
        id INTEGER PRIMARY KEY,
        pain_point TEXT NOT NULL,
        source_subreddit TEXT,
        hook TEXT NOT NULL,
        problem TEXT NOT NULL,
        insight TEXT NOT NULL,
        cta TEXT NOT NULL,
        format TEXT DEFAULT 'talking_head',
        generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    CREATE TABLE IF NOT EXISTS reports (
        id INTEGER PRIMARY KEY,
        type TEXT NOT NULL,
        period_start TIMESTAMP,
        period_end TIMESTAMP,
        body_md TEXT NOT NULL,
        sent_via_telegram INTEGER DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    CREATE TABLE IF NOT EXISTS opportunities (
        id INTEGER PRIMARY KEY,
        type TEXT,
        title TEXT NOT NULL,
        score REAL,
        source_url TEXT,
        notes TEXT,
        alerted_at TIMESTAMP,
        status TEXT DEFAULT 'new'
    );
    CREATE TABLE IF NOT EXISTS employees (
        id INTEGER PRIMARY KEY,
        name TEXT UNIQUE NOT NULL,
        type TEXT NOT NULL,
        enabled INTEGER DEFAULT 1,
        last_run_at TIMESTAMP,
        last_status TEXT
    );
    -- ── Expansion tables ─────────────────────────────────────────────────────
    CREATE TABLE IF NOT EXISTS hook_performance (
        id INTEGER PRIMARY KEY,
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
        recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    CREATE TABLE IF NOT EXISTS swipe_file (
        id INTEGER PRIMARY KEY,
        source_url TEXT UNIQUE NOT NULL,
        platform TEXT,
        collection TEXT,
        hook_text TEXT,
        topic TEXT,
        creator_handle TEXT,
        content_format TEXT,
        emotional_trigger TEXT,
        narrative_style TEXT,
        date_saved TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        personal_rating INTEGER DEFAULT 0,
        notes TEXT,
        analyzed INTEGER DEFAULT 0,
        chroma_id TEXT
    );
    CREATE TABLE IF NOT EXISTS opinion_topics (
        id INTEGER PRIMARY KEY,
        topic TEXT NOT NULL,
        type TEXT DEFAULT 'question',
        source TEXT,
        relevance_score REAL DEFAULT 0.0,
        generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        used INTEGER DEFAULT 0
    );
    CREATE TABLE IF NOT EXISTS upload_queue (
        id INTEGER PRIMARY KEY,
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
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    CREATE TABLE IF NOT EXISTS employee_activity_log (
        id INTEGER PRIMARY KEY,
        employee TEXT NOT NULL,
        action TEXT NOT NULL,
        detail TEXT,
        logged_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    CREATE TABLE IF NOT EXISTS daily_briefs (
        id INTEGER PRIMARY KEY,
        body_md TEXT NOT NULL,
        generated_by TEXT DEFAULT 'Dwight',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)
    conn.commit()

    # Migrations — safe to re-run
    for col, coltype in [("thumbnail_url", "TEXT"), ("ai_analysis", "TEXT")]:
        try:
            conn.execute(f"ALTER TABLE competitor_posts ADD COLUMN {col} {coltype}")
            conn.commit()
        except Exception:
            pass  # column already exists

def seed_competitors(conn: sqlite3.Connection, handles: list, platform: str) -> None:
    conn.executemany(
        "INSERT OR IGNORE INTO competitors (handle, platform) VALUES (?, ?)",
        [(h, platform) for h in handles]
    )
    conn.commit()

def seed_employees(conn: sqlite3.Connection, employees: dict) -> None:
    for name, cfg in employees.items():
        conn.execute(
            "INSERT OR IGNORE INTO employees (name, type, enabled) VALUES (?, ?, ?)",
            (name, cfg["type"], 1 if cfg.get("enabled", True) else 0)
        )
    conn.commit()

def update_employee_status(conn: sqlite3.Connection, name: str, status: str) -> None:
    conn.execute(
        "UPDATE employees SET last_run_at=CURRENT_TIMESTAMP, last_status=? WHERE name=?",
        (status, name)
    )
    conn.commit()
