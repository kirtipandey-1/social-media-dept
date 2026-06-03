from unittest.mock import patch, MagicMock

def test_score_topic_returns_0_to_100():
    from mcp_servers.radar_server import score_topic
    with patch("mcp_servers.radar_server.call_ollama",
               return_value="Score: 82\nThis topic is trending"):
        score = score_topic("lo-fi beats")
    assert 0 <= score <= 100

def test_score_topic_defaults_50_on_no_match():
    from mcp_servers.radar_server import score_topic
    with patch("mcp_servers.radar_server.call_ollama", return_value="no score here"):
        score = score_topic("anything")
    assert score == 50

def test_scan_opportunities_writes_to_db(tmp_path):
    from mcp_servers.radar_server import scan_opportunities
    from db.sqlite_db import get_connection, init_schema
    conn = get_connection(str(tmp_path / "t.db"))
    init_schema(conn)
    conn.execute("""INSERT INTO trends (source, topic, signal_strength, detected_at)
        VALUES ('reddit','lo-fi beats tutorial',0.9,'2026-06-01')""")
    conn.commit()
    with patch("mcp_servers.radar_server.get_db_connection", return_value=conn), \
         patch("mcp_servers.radar_server.score_topic", return_value=85):
        result = scan_opportunities()
    assert result["opportunities_found"] >= 1
    assert result["trends_checked"] >= 1
