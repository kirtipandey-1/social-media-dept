import pytest
from db.duckdb_db import get_connection, init_schema, upsert_post_performance

def test_init_schema_creates_tables(tmp_path):
    conn = get_connection(str(tmp_path / "test.duckdb"))
    init_schema(conn)
    tables = conn.execute("SHOW TABLES").fetchall()
    names = {r[0] for r in tables}
    assert {"post_performance", "daily_kpis"}.issubset(names)

def test_upsert_post_performance_inserts(tmp_path):
    conn = get_connection(str(tmp_path / "test.duckdb"))
    init_schema(conn)
    upsert_post_performance(conn, {
        "post_url": "https://instagram.com/p/abc",
        "platform": "instagram",
        "views": 1000, "likes": 50, "saves": 20,
        "shares": 5, "comments": 10, "watch_time_pct": 0.65,
        "posted_at": "2026-06-01"
    })
    row = conn.execute(
        "SELECT views FROM post_performance WHERE post_url='https://instagram.com/p/abc'"
    ).fetchone()
    assert row[0] == 1000

def test_upsert_post_performance_updates_on_conflict(tmp_path):
    conn = get_connection(str(tmp_path / "test.duckdb"))
    init_schema(conn)
    data = {"post_url": "https://instagram.com/p/xyz", "platform": "instagram",
            "views": 500, "likes": 10, "saves": 5, "shares": 0, "comments": 3,
            "watch_time_pct": 0.5, "posted_at": "2026-06-01"}
    upsert_post_performance(conn, data)
    data["views"] = 9999
    upsert_post_performance(conn, data)
    rows = conn.execute("SELECT views FROM post_performance WHERE post_url='https://instagram.com/p/xyz'").fetchall()
    assert len(rows) == 1
    assert rows[0][0] == 9999
