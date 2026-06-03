import pytest
from unittest.mock import patch, MagicMock


# ─── Task 8: Reddit RSS ───────────────────────────────────────────────────────

def _make_mock_entry(link="https://reddit.com/r/beatmakers/comments/abc123/title/"):
    e = MagicMock()
    e.id = "https://reddit.com/r/beatmakers/comments/abc123/title/"
    e.link = link
    e.title = "Why can't I get my mix to translate?"
    e.summary = "I mix in headphones and..."
    e.published_parsed = (2026, 6, 1, 10, 0, 0, 0, 0, 0)
    return e

def test_fetch_reddit_rss_returns_posts():
    mock_feed = MagicMock()
    mock_feed.entries = [_make_mock_entry()]
    with patch("feedparser.parse", return_value=mock_feed):
        from workers.research_scraper import fetch_reddit_rss
        posts = fetch_reddit_rss("beatmakers", limit=25)
    assert len(posts) == 1
    assert posts[0]["reddit_id"] == "abc123"
    assert posts[0]["subreddit"] == "beatmakers"
    assert "mix" in posts[0]["title"].lower()

def test_save_reddit_posts(tmp_path):
    from workers.research_scraper import save_reddit_posts
    from db.sqlite_db import get_connection, init_schema
    conn = get_connection(str(tmp_path / "t.db"))
    init_schema(conn)
    posts = [{"reddit_id": "abc", "subreddit": "beatmakers",
               "title": "Test", "body": "body",
               "url": "http://x", "upvotes": 10,
               "num_comments": 5, "posted_at": "2026-06-01"}]
    saved = save_reddit_posts(conn, posts)
    assert saved == 1
    rows = conn.execute("SELECT reddit_id FROM reddit_posts").fetchall()
    assert rows[0][0] == "abc"

def test_save_reddit_posts_ignores_duplicates(tmp_path):
    from workers.research_scraper import save_reddit_posts
    from db.sqlite_db import get_connection, init_schema
    conn = get_connection(str(tmp_path / "t.db"))
    init_schema(conn)
    p = [{"reddit_id": "dup", "subreddit": "beatmakers", "title": "T",
           "body": "b", "url": "http://x", "upvotes": 1,
           "num_comments": 0, "posted_at": None}]
    save_reddit_posts(conn, p)
    save_reddit_posts(conn, p)  # second call
    count = conn.execute("SELECT COUNT(*) FROM reddit_posts").fetchone()[0]
    assert count == 1


# ─── Task 9: Instagram helpers ───────────────────────────────────────────────

def test_parse_post_element_normalises_numbers():
    from workers.research_scraper import parse_post_element
    result = parse_post_element({
        "url": "https://instagram.com/p/abc",
        "caption": "Test caption",
        "views": "45.2K",
        "likes": "1,230",
    })
    assert result["post_url"] == "https://instagram.com/p/abc"
    assert result["views"] == 45200
    assert result["likes"] == 1230
    assert result["comments"] == 0

def test_parse_post_element_handles_millions():
    from workers.research_scraper import parse_post_element
    result = parse_post_element({"url": "http://x", "views": "1.2M"})
    assert result["views"] == 1_200_000

# ─── Task 10: ResearchScraper class ──────────────────────────────────────────

def test_save_competitor_posts(tmp_path):
    from workers.research_scraper import save_competitor_posts
    from db.sqlite_db import get_connection, init_schema, seed_competitors
    conn = get_connection(str(tmp_path / "t.db"))
    init_schema(conn)
    seed_competitors(conn, ["sndtrak"], "instagram")
    posts = [{"post_url": "https://instagram.com/p/abc", "caption": "test",
               "views": 1000, "likes": 50, "comments": 10, "saves": 20}]
    saved = save_competitor_posts(conn, "sndtrak", posts)
    assert saved == 1
    row = conn.execute("SELECT views FROM competitor_posts").fetchone()
    assert row[0] == 1000

def test_save_competitor_posts_skips_unknown_handle(tmp_path):
    from workers.research_scraper import save_competitor_posts
    from db.sqlite_db import get_connection, init_schema
    conn = get_connection(str(tmp_path / "t.db"))
    init_schema(conn)
    result = save_competitor_posts(conn, "nobody_handle", [{"post_url": "http://x"}])
    assert result == 0
