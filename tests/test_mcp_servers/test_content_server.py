from unittest.mock import patch, MagicMock

def test_get_pain_points_from_db(tmp_path):
    from mcp_servers.content_server import get_pain_points
    from db.sqlite_db import get_connection, init_schema
    conn = get_connection(str(tmp_path / "t.db"))
    init_schema(conn)
    conn.execute("""INSERT INTO reddit_posts
        (reddit_id, subreddit, title, body, upvotes, num_comments, url, posted_at)
        VALUES ('x1','beatmakers','Why does my mix sound bad in the car',
                'I mix in headphones...',150,30,'http://x','2026-06-01')""")
    conn.commit()
    with patch("mcp_servers.content_server.get_db_connection", return_value=conn):
        points = get_pain_points(niche="beatmaking", limit=5)
    assert len(points) >= 1
    assert "mix" in points[0]["title"].lower()

def test_get_pain_points_filters_by_niche(tmp_path):
    from mcp_servers.content_server import get_pain_points
    from db.sqlite_db import get_connection, init_schema
    conn = get_connection(str(tmp_path / "t.db"))
    init_schema(conn)
    conn.execute("""INSERT INTO reddit_posts
        (reddit_id, subreddit, title, body, upvotes, num_comments, url, posted_at)
        VALUES ('b1','beatmakers','Beat mixing tip',
                'body',100,5,'http://x','2026-06-01')""")
    conn.execute("""INSERT INTO reddit_posts
        (reddit_id, subreddit, title, body, upvotes, num_comments, url, posted_at)
        VALUES ('z1','python','Python tip',
                'body',200,10,'http://y','2026-06-01')""")
    conn.commit()
    with patch("mcp_servers.content_server.get_db_connection", return_value=conn):
        points = get_pain_points(niche="beatmaking", limit=10)
    subreddits = {p["subreddit"] for p in points}
    assert "python" not in subreddits

def test_generate_script_structure():
    from mcp_servers.content_server import generate_script
    mock_script = "HOOK: Nobody told me this about mixing\nPROBLEM: Every producer struggles\nINSIGHT: Here is the fix\nCTA: Save this"
    with patch("mcp_servers.content_server.call_ollama", return_value=mock_script), \
         patch("mcp_servers.content_server.get_db_connection") as mock_db:
        mock_db.return_value.execute.return_value = MagicMock()
        script = generate_script("my mix sounds bad in the car", 60)
    assert script["hook"]
    assert script["problem"]
    assert script["insight"]
    assert script["cta"]
