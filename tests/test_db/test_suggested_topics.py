import sys; sys.path.insert(0, ".")
import unittest.mock as mock

def test_get_suggested_topics_returns_list():
    """get_suggested_topics should return a list of strings."""
    with mock.patch("streamlit.cache_data", lambda **kw: lambda f: f):
        with mock.patch("dashboard.db_helpers.get_connection") as mc:
            conn = mock.MagicMock()
            # trends query returns 2 topics, reddit query returns 1
            conn.execute.return_value.fetchall.side_effect = [
                [("boom bap",), ("sample flipping",)],
                [("Best drum patterns for boom bap",)],
            ]
            mc.return_value = conn
            import importlib
            import dashboard.db_helpers as dbh
            importlib.reload(dbh)
            result = dbh.get_suggested_topics(limit=5)
    assert isinstance(result, list)
    assert len(result) >= 2
    assert all(isinstance(t, str) for t in result)
