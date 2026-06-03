def test_format_for_telegram_trims_to_limit():
    from workers.notifier import format_for_telegram
    long_text = "x" * 5000
    result = format_for_telegram(long_text)
    assert len(result) <= 4096

def test_format_for_telegram_passes_short():
    from workers.notifier import format_for_telegram
    text = "## Daily Report\n- Trend: lo-fi beats"
    result = format_for_telegram(text)
    assert result == text

def test_telegram_notifier_skips_when_not_configured(monkeypatch):
    from workers.notifier import TelegramNotifier
    import os
    monkeypatch.setenv("SOCIALDEPT_CONFIG", "/tmp/nonexistent_socialdept.toml")
    # create minimal toml
    import tempfile, pathlib
    tmp = pathlib.Path(tempfile.mktemp(suffix=".toml"))
    tmp.write_text('[telegram]\nbot_token=""\nchat_id=""\n')
    monkeypatch.setenv("SOCIALDEPT_CONFIG", str(tmp))
    n = TelegramNotifier("daily")
    # should not raise even with empty credentials — just returns 'skipped'
    with __import__("unittest.mock", fromlist=["patch"]).patch(
        "mcp_servers.reports_server.generate_daily_report", return_value="ok"
    ):
        result = n.run()
    assert result == "skipped: not configured"
