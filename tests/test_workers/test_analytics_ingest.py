def test_parse_insights_text_extracts_numbers():
    from workers.analytics_ingest import parse_insights_text
    text = """
    Views: 45,200
    Likes: 1,230
    Saves: 890
    Comments: 145
    Reach: 62,000
    """
    result = parse_insights_text(text)
    assert result["views"] == 45200
    assert result["saves"] == 890
    assert result["likes"] == 1230

def test_parse_insights_text_handles_missing():
    from workers.analytics_ingest import parse_insights_text
    result = parse_insights_text("Views: 1000")
    assert result["views"] == 1000
    assert result["saves"] == 0
