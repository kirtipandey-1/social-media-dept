from unittest.mock import patch, MagicMock


def test_add_swipe_entry(tmp_path):
    from mcp_servers.swipe_server import add_swipe_entry
    from db.sqlite_db import get_connection, init_schema
    conn = get_connection(str(tmp_path / "t.db"))
    init_schema(conn)
    with patch("mcp_servers.swipe_server.get_db_connection", return_value=conn):
        result = add_swipe_entry(
            source_url="https://instagram.com/p/abc",
            platform="instagram",
            collection="content",
            hook_text="Nobody told me this about mixing",
            topic="mixing",
            creator_handle="sndtrak",
            content_format="talking_head",
            emotional_trigger="curiosity",
            personal_rating=5,
            notes="Great hook structure"
        )
    assert result["saved"] is True
    row = conn.execute("SELECT hook_text FROM swipe_file WHERE source_url='https://instagram.com/p/abc'").fetchone()
    assert "mixing" in row[0].lower()


def test_search_swipe_file(tmp_path):
    from mcp_servers.swipe_server import add_swipe_entry, search_swipe_file
    from db.sqlite_db import get_connection, init_schema
    conn = get_connection(str(tmp_path / "t.db"))
    init_schema(conn)
    with patch("mcp_servers.swipe_server.get_db_connection", return_value=conn):
        add_swipe_entry("http://x.com/1", "instagram", "content",
                        hook_text="Bass tutorial hook", topic="bass")
        results = search_swipe_file("bass")
    assert len(results) >= 1
    assert any("bass" in r.get("topic", "").lower() or "bass" in r.get("hook_text", "").lower() for r in results)


def test_get_top_saved_patterns(tmp_path):
    from mcp_servers.swipe_server import add_swipe_entry, get_top_saved_patterns
    from db.sqlite_db import get_connection, init_schema
    conn = get_connection(str(tmp_path / "t.db"))
    init_schema(conn)
    with patch("mcp_servers.swipe_server.get_db_connection", return_value=conn):
        for i in range(3):
            add_swipe_entry(f"http://x.com/{i}", "instagram", "content",
                            content_format="talking_head", topic="mixing")
        patterns = get_top_saved_patterns()
    assert len(patterns) >= 1
