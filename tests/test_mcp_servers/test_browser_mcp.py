from unittest.mock import patch, MagicMock


def test_get_unseen_urls_empty_on_no_saved_posts(tmp_path):
    from mcp_servers.browser_mcp import get_unseen_saved_urls
    from db.sqlite_db import get_connection, init_schema
    conn = get_connection(str(tmp_path / "t.db"))
    init_schema(conn)
    with patch("mcp_servers.browser_mcp.get_db_connection", return_value=conn):
        unseen = get_unseen_saved_urls(["http://insta.com/p/1", "http://insta.com/p/2"])
    assert len(unseen) == 2  # none in DB yet, both unseen


def test_get_unseen_urls_filters_seen(tmp_path):
    from mcp_servers.browser_mcp import get_unseen_saved_urls
    from db.sqlite_db import get_connection, init_schema
    conn = get_connection(str(tmp_path / "t.db"))
    init_schema(conn)
    conn.execute("INSERT INTO saved_post_analysis (post_url, collection) VALUES ('http://insta.com/p/1','content')")
    conn.commit()
    with patch("mcp_servers.browser_mcp.get_db_connection", return_value=conn):
        unseen = get_unseen_saved_urls(["http://insta.com/p/1", "http://insta.com/p/2"])
    assert len(unseen) == 1
    assert "p/2" in unseen[0]


def test_mark_url_analyzed(tmp_path):
    from mcp_servers.browser_mcp import mark_url_analyzed
    from db.sqlite_db import get_connection, init_schema
    conn = get_connection(str(tmp_path / "t.db"))
    init_schema(conn)
    with patch("mcp_servers.browser_mcp.get_db_connection", return_value=conn):
        mark_url_analyzed("http://x.com/p/abc", "content", "hook text", "visual notes")
    row = conn.execute("SELECT hook_text FROM saved_post_analysis").fetchone()
    assert row[0] == "hook text"


def test_log_upload_records_to_db(tmp_path):
    from mcp_servers.browser_mcp import log_upload_result
    from db.sqlite_db import get_connection, init_schema
    conn = get_connection(str(tmp_path / "t.db"))
    init_schema(conn)
    with patch("mcp_servers.browser_mcp.get_db_connection", return_value=conn):
        log_upload_result("/path/video.mp4", "My Beat", "success")
    row = conn.execute("SELECT status FROM upload_queue WHERE title='My Beat'").fetchone()
    assert row[0] == "success"
