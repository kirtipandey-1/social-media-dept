from unittest.mock import patch

def test_cluster_saved_content_returns_dict(tmp_path):
    from mcp_servers.learning_server import cluster_saved_content
    from db.sqlite_db import get_connection, init_schema
    conn = get_connection(str(tmp_path / "t.db"))
    init_schema(conn)
    for i in range(5):
        conn.execute("""INSERT INTO swipe_file
            (source_url, platform, topic, emotional_trigger)
            VALUES (?,?,?,?)""",
            (f"http://x/{i}", "instagram", "mixing", "curiosity"))
    conn.commit()
    with patch("mcp_servers.learning_server.get_db_connection", return_value=conn), \
         patch("mcp_servers.learning_server.call_ollama",
               return_value="CLUSTERS:\n- mixing: 5 items\n- curiosity trigger dominant"):
        result = cluster_saved_content()
    assert isinstance(result, dict)
    assert "clusters" in result or "analysis" in result

def test_get_taste_evolution_returns_string(tmp_path):
    from mcp_servers.learning_server import get_taste_evolution
    from db.sqlite_db import get_connection, init_schema
    conn = get_connection(str(tmp_path / "t.db"))
    init_schema(conn)
    with patch("mcp_servers.learning_server.get_db_connection", return_value=conn), \
         patch("mcp_servers.learning_server.call_ollama", return_value="Your taste is evolving toward lo-fi"):
        result = get_taste_evolution()
    assert isinstance(result, str)
