from unittest.mock import patch, MagicMock

def test_generate_daily_brief_returns_string(tmp_path):
    from mcp_servers.strategy_server import generate_daily_brief
    from db.sqlite_db import get_connection, init_schema
    conn = get_connection(str(tmp_path / "t.db"))
    init_schema(conn)
    with patch("mcp_servers.strategy_server.get_db_connection", return_value=conn), \
         patch("mcp_servers.strategy_server.call_ollama",
               return_value="## Dwight's Brief\n**Recommended Post Today:** Make a beat drop video"):
        brief = generate_daily_brief()
    assert isinstance(brief, str)
    assert len(brief) > 20

def test_generate_daily_brief_saves_to_db(tmp_path):
    from mcp_servers.strategy_server import generate_daily_brief
    from db.sqlite_db import get_connection, init_schema
    conn = get_connection(str(tmp_path / "t.db"))
    init_schema(conn)
    with patch("mcp_servers.strategy_server.get_db_connection", return_value=conn), \
         patch("mcp_servers.strategy_server.call_ollama", return_value="## Brief content"):
        generate_daily_brief()
    row = conn.execute("SELECT body_md FROM daily_briefs LIMIT 1").fetchone()
    assert row is not None
    assert "Brief" in row[0]
