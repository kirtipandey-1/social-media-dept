from unittest.mock import patch, MagicMock


def test_generate_hooks_returns_list():
    from mcp_servers.hooks_server import generate_hooks
    with patch("mcp_servers.hooks_server.call_ollama",
               return_value="1. Nobody told me this\n2. Stop doing this\n3. Here is why"):
        with patch("mcp_servers.hooks_server.get_hooks_collection") as mock_col:
            mock_col.return_value.upsert = MagicMock()
            mock_col.return_value.count = MagicMock(return_value=0)
            hooks = generate_hooks("trap beat", count=3, save=False)
    assert isinstance(hooks, list)
    assert len(hooks) == 3
    assert all(isinstance(h, str) for h in hooks)


def test_generate_hooks_parses_numbered_list():
    from mcp_servers.hooks_server import _parse_numbered_list
    raw = "1. First hook\n2. Second hook\n3. Third hook"
    result = _parse_numbered_list(raw)
    assert result == ["First hook", "Second hook", "Third hook"]


def test_classify_hook_categories():
    from mcp_servers.hooks_server import _classify_hook
    assert _classify_hook("nobody told me this secret") == "curiosity"
    assert _classify_hook("stop making this mistake") == "pain_point"
    assert _classify_hook("I made $10k from this beat") == "flex"


def test_search_hooks_fn_returns_results(tmp_path):
    from mcp_servers.hooks_server import search_hooks_fn
    from db.chroma_db import get_collection, upsert_hook
    col = get_collection(str(tmp_path / "chroma"))
    upsert_hook(col, "Stop making this mixing mistake")
    with patch("mcp_servers.hooks_server.get_hooks_collection", return_value=col):
        results = search_hooks_fn("mixing mistake", limit=1)
    assert len(results) == 1
    assert "mixing" in results[0]["document"].lower()


def test_get_top_hooks_sorted_by_score(tmp_path):
    from mcp_servers.hooks_server import get_top_hooks
    from db.chroma_db import get_collection, upsert_hook
    col = get_collection(str(tmp_path / "chroma"))
    upsert_hook(col, "Low score hook", engagement_score=10.0)
    upsert_hook(col, "High score hook", engagement_score=90.0)
    with patch("mcp_servers.hooks_server.get_hooks_collection", return_value=col):
        top = get_top_hooks(limit=2)
    assert top[0]["score"] >= top[1]["score"]


def test_cluster_hooks_returns_string(tmp_path):
    from mcp_servers.hooks_server import cluster_hooks
    from db.chroma_db import get_collection, upsert_hook
    col = get_collection(str(tmp_path / "chroma"))
    for i in range(6):
        upsert_hook(col, f"Hook number {i}", category="curiosity")
    with patch("mcp_servers.hooks_server.get_hooks_collection", return_value=col):
        result = cluster_hooks()
    assert isinstance(result, str)
    assert "curiosity" in result.lower()
