import pytest
from db.chroma_db import get_collection, upsert_hook, search_hooks

def test_upsert_and_search(tmp_path):
    col = get_collection(str(tmp_path / "chroma"))
    upsert_hook(col, "Nobody told me this about mixing bass",
                category="pain_point", source="generated")
    results = search_hooks(col, "mixing bass", limit=1)
    assert len(results) == 1
    assert "mixing" in results[0]["document"].lower()

def test_upsert_stores_metadata(tmp_path):
    col = get_collection(str(tmp_path / "chroma"))
    upsert_hook(col, "Stop doing this when producing",
                category="pain_point", source="generated",
                engagement_score=85.0, status="winning")
    results = search_hooks(col, "producing", limit=1)
    assert results[0]["metadata"]["category"] == "pain_point"
    assert results[0]["metadata"]["status"] == "winning"

def test_search_returns_empty_on_empty_collection(tmp_path):
    col = get_collection(str(tmp_path / "chroma"))
    results = search_hooks(col, "anything", limit=5)
    assert results == []
