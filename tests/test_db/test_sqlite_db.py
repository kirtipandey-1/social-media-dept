import pytest
from db.sqlite_db import get_connection, init_schema, seed_competitors, seed_employees, update_employee_status

def test_init_schema_creates_all_tables(tmp_path):
    conn = get_connection(str(tmp_path / "test.db"))
    init_schema(conn)
    tables = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table'"
    ).fetchall()
    names = {r[0] for r in tables}
    expected = {
        "competitors","competitor_posts","trends","reddit_posts",
        "saved_post_analysis","comments","comment_insights",
        "scripts","reports","opportunities","employees"
    }
    assert expected.issubset(names), f"Missing tables: {expected - names}"

def test_seed_competitors_inserts_rows(tmp_path):
    conn = get_connection(str(tmp_path / "test.db"))
    init_schema(conn)
    seed_competitors(conn, ["sndtrak", "mpcchop"], "instagram")
    rows = conn.execute("SELECT handle FROM competitors ORDER BY handle").fetchall()
    assert {r[0] for r in rows} == {"sndtrak", "mpcchop"}

def test_seed_competitors_is_idempotent(tmp_path):
    conn = get_connection(str(tmp_path / "test.db"))
    init_schema(conn)
    seed_competitors(conn, ["sndtrak"], "instagram")
    seed_competitors(conn, ["sndtrak"], "instagram")  # second call same data
    rows = conn.execute("SELECT handle FROM competitors").fetchall()
    assert len(rows) == 1  # no duplicates

def test_seed_employees(tmp_path):
    conn = get_connection(str(tmp_path / "test.db"))
    init_schema(conn)
    employees = {
        "hooks_server": {"type": "mcp_server", "enabled": True},
        "research_scraper": {"type": "worker", "enabled": True},
    }
    seed_employees(conn, employees)
    rows = conn.execute("SELECT name, type FROM employees ORDER BY name").fetchall()
    assert len(rows) == 2
    assert rows[0][0] == "hooks_server"
    assert rows[0][1] == "mcp_server"

def test_update_employee_status(tmp_path):
    conn = get_connection(str(tmp_path / "test.db"))
    init_schema(conn)
    seed_employees(conn, {"research_scraper": {"type": "worker", "enabled": True}})
    update_employee_status(conn, "research_scraper", "ok")
    row = conn.execute("SELECT last_status FROM employees WHERE name='research_scraper'").fetchone()
    assert row[0] == "ok"
