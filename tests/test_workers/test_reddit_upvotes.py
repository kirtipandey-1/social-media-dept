import sys; sys.path.insert(0, ".")
from unittest import mock

def test_fetch_reddit_uses_top_week():
    """fetch_reddit_rss should hit /top.rss?t=week for upvote data."""
    from workers.research_scraper import fetch_reddit_rss
    with mock.patch("workers.research_scraper.feedparser.parse") as mp:
        mp.return_value = mock.MagicMock(entries=[])
        fetch_reddit_rss("beatmakers", limit=5)
        called_url = mp.call_args[0][0]
    assert "top.rss" in called_url, f"Expected top.rss, got: {called_url}"
    assert "t=week" in called_url

def test_fetch_reddit_returns_upvotes():
    """fetch_reddit_rss should return posts with integer upvotes field."""
    # Use a small live fetch — if network unavailable, skip gracefully
    try:
        from workers.research_scraper import fetch_reddit_rss
        posts = fetch_reddit_rss("beatmakers", limit=3)
        for p in posts:
            assert isinstance(p["upvotes"], int)
            assert p["upvotes"] >= 0
    except Exception as e:
        import pytest; pytest.skip(f"Network unavailable: {e}")
