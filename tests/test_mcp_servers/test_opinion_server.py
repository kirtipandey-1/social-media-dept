from unittest.mock import patch

def test_generate_questions_returns_list():
    from mcp_servers.opinion_server import generate_questions
    with patch("mcp_servers.opinion_server.call_ollama",
               return_value="1. Is sampling dead?\n2. Do producers need music theory?\n3. Best DAW?"):
        with patch("mcp_servers.opinion_server.get_db_connection") as mock_db:
            import sqlite3; tmp_conn = sqlite3.connect(":memory:")
            tmp_conn.execute("CREATE TABLE opinion_topics (id INTEGER PRIMARY KEY, topic TEXT NOT NULL, type TEXT, source TEXT, relevance_score REAL, generated_at TIMESTAMP, used INTEGER DEFAULT 0)")
            tmp_conn.execute("CREATE TABLE employee_activity_log (id INTEGER PRIMARY KEY, employee TEXT, action TEXT, detail TEXT, logged_at TIMESTAMP)")
            mock_db.return_value = tmp_conn
            results = generate_questions(count=3)
    assert isinstance(results, list)
    assert len(results) >= 1

def test_generate_hot_takes_returns_list():
    from mcp_servers.opinion_server import generate_hot_takes
    with patch("mcp_servers.opinion_server.call_ollama",
               return_value="1. Trap beats are dying\n2. Lo-fi is oversaturated\n3. NFTs ruined music"):
        with patch("mcp_servers.opinion_server.get_db_connection") as mock_db:
            import sqlite3; tmp_conn = sqlite3.connect(":memory:")
            tmp_conn.execute("CREATE TABLE opinion_topics (id INTEGER PRIMARY KEY, topic TEXT NOT NULL, type TEXT, source TEXT, relevance_score REAL, generated_at TIMESTAMP, used INTEGER DEFAULT 0)")
            tmp_conn.execute("CREATE TABLE employee_activity_log (id INTEGER PRIMARY KEY, employee TEXT, action TEXT, detail TEXT, logged_at TIMESTAMP)")
            mock_db.return_value = tmp_conn
            takes = generate_hot_takes(count=3)
    assert isinstance(takes, list)
