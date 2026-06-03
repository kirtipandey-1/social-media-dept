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
    """)
    conn.commit()

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
