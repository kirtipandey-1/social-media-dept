import sys; sys.path.insert(0, ".")
from workers.research_scraper import parse_post_element

def test_parse_post_element_has_thumbnail():
    result = parse_post_element({"url": "https://instagram.com/p/abc", "thumbnail_url": "https://cdn.instagram.com/thumb.jpg", "caption": "test"})
    assert result["thumbnail_url"] == "https://cdn.instagram.com/thumb.jpg"

def test_parse_post_element_missing_thumbnail_is_empty():
    result = parse_post_element({"url": "https://instagram.com/p/abc"})
    assert result.get("thumbnail_url", "") == ""
