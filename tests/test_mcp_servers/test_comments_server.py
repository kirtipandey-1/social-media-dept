from unittest.mock import patch, MagicMock
import json

def test_classify_comment_returns_category():
    from mcp_servers.comments_server import classify_comment
    with patch("mcp_servers.comments_server.call_ollama",
               return_value='{"category":"pain_point","sentiment":"negative"}'):
        result = classify_comment("I can't get my 808s to punch through the mix")
    assert result["category"] == "pain_point"
    assert result["sentiment"] == "negative"

def test_classify_comment_handles_bad_json():
    from mcp_servers.comments_server import classify_comment
    with patch("mcp_servers.comments_server.call_ollama", return_value="not json at all"):
        result = classify_comment("some comment")
    assert result["category"] == "other"
    assert result["sentiment"] == "neutral"

def test_get_pain_points_from_insights(tmp_path):
    from mcp_servers.comments_server import get_pain_points
    from db.sqlite_db import get_connection, init_schema
    conn = get_connection(str(tmp_path / "t.db"))
    init_schema(conn)
    conn.execute("""INSERT INTO comment_insights
        (category, insight, frequency, example_comment)
        VALUES ('pain_point','Mixing bass is hard',5,'My bass always sounds muddy')""")
    conn.commit()
    with patch("mcp_servers.comments_server.get_db_connection", return_value=conn):
        points = get_pain_points(5)
    assert len(points) == 1
    assert "bass" in points[0]["insight"].lower()
