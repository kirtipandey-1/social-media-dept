import duckdb
from pathlib import Path

DB_PATH = Path.home() / "social-media-dept" / "db" / "analytics.duckdb"

def get_connection(path: str | None = None) -> duckdb.DuckDBPyConnection:
    p = path or str(DB_PATH)
    Path(p).parent.mkdir(parents=True, exist_ok=True)
    return duckdb.connect(p)

def init_schema(conn: duckdb.DuckDBPyConnection) -> None:
    conn.execute("""
    CREATE TABLE IF NOT EXISTS post_performance (
        post_url VARCHAR NOT NULL,
        platform VARCHAR,
        views BIGINT,
        likes INTEGER,
        saves INTEGER,
        shares INTEGER,
        comments INTEGER,
        watch_time_pct FLOAT,
        posted_at TIMESTAMP,
        recorded_at TIMESTAMP DEFAULT NOW(),
        PRIMARY KEY (post_url)
    )
    """)
    conn.execute("""
    CREATE TABLE IF NOT EXISTS daily_kpis (
        date DATE NOT NULL,
        platform VARCHAR NOT NULL,
        total_views BIGINT,
        avg_engagement_rate FLOAT,
        top_post_url VARCHAR,
        follower_delta INTEGER,
        PRIMARY KEY (date, platform)
    )
    """)

def upsert_post_performance(conn: duckdb.DuckDBPyConnection, data: dict) -> None:
    conn.execute("""
    INSERT INTO post_performance
        (post_url, platform, views, likes, saves, shares, comments, watch_time_pct, posted_at)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    ON CONFLICT (post_url) DO UPDATE SET
        views=excluded.views, likes=excluded.likes, saves=excluded.saves,
        shares=excluded.shares, comments=excluded.comments,
        watch_time_pct=excluded.watch_time_pct, recorded_at=NOW()
    """, [data["post_url"], data.get("platform", "instagram"),
          data.get("views", 0), data.get("likes", 0), data.get("saves", 0),
          data.get("shares", 0), data.get("comments", 0),
          data.get("watch_time_pct", 0.0), data.get("posted_at")])
