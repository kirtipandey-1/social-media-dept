from unittest.mock import patch, MagicMock

def test_generate_daily_report_returns_markdown(tmp_path):
    from mcp_servers.reports_server import generate_daily_report
    from db.sqlite_db import get_connection, init_schema
    conn = get_connection(str(tmp_path / "t.db"))
    init_schema(conn)
    with patch("mcp_servers.reports_server.get_db_connection", return_value=conn), \
         patch("mcp_servers.reports_server.call_ollama",
               return_value="## Daily Report\nTop trend: lo-fi beats"):
        report = generate_daily_report()
    assert "##" in report
    assert isinstance(report, str)
    assert len(report) > 20

def test_generate_weekly_report_returns_markdown(tmp_path):
    from mcp_servers.reports_server import generate_weekly_report
    from db.sqlite_db import get_connection, init_schema
    conn = get_connection(str(tmp_path / "t.db"))
    init_schema(conn)
    with patch("mcp_servers.reports_server.get_db_connection", return_value=conn), \
         patch("mcp_servers.reports_server.call_ollama",
               return_value="## Weekly Review\n- Trend: lo-fi"):
        report = generate_weekly_report()
    assert isinstance(report, str)
    assert len(report) > 10

def test_generate_monthly_report_returns_markdown(tmp_path):
    from mcp_servers.reports_server import generate_monthly_report
    from db.sqlite_db import get_connection, init_schema
    conn = get_connection(str(tmp_path / "t.db"))
    init_schema(conn)
    with patch("mcp_servers.reports_server.get_db_connection", return_value=conn), \
         patch("mcp_servers.reports_server.call_ollama",
               return_value="## Monthly Audit\nGrowth: +12%"):
        report = generate_monthly_report()
    assert isinstance(report, str)
    assert len(report) > 10

def test_get_report_retrieves_saved(tmp_path):
    from mcp_servers.reports_server import get_report
    from db.sqlite_db import get_connection, init_schema
    conn = get_connection(str(tmp_path / "t.db"))
    init_schema(conn)
    conn.execute("INSERT INTO reports (type, body_md) VALUES ('daily','## Saved Report')")
    conn.commit()
    with patch("mcp_servers.reports_server.get_db_connection", return_value=conn):
        result = get_report("daily")
    assert "Saved Report" in result
