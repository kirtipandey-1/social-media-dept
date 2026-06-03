from unittest.mock import patch, MagicMock

def test_orchestrator_runs_all_phases():
    with patch("workers.research_scraper.ResearchScraper") as MockR, \
         patch("workers.analytics_ingest.AnalyticsIngest") as MockA, \
         patch("mcp_servers.hooks_server.generate_hooks", return_value=[]) as MockH, \
         patch("mcp_servers.comments_server.analyze_comments", return_value={}) as MockC, \
         patch("mcp_servers.radar_server.scan_opportunities", return_value={"opportunities_found":0,"trends_checked":0}) as MockO, \
         patch("mcp_servers.reports_server.generate_daily_report", return_value="ok") as MockRep, \
         patch("db.sqlite_db.get_connection") as mock_db:
        MockR.return_value.execute = MagicMock()
        MockA.return_value.execute = MagicMock()
        mock_conn = MagicMock()
        mock_conn.execute.return_value.fetchall.return_value = []
        mock_db.return_value = mock_conn
        from orchestrator import run_pipeline
        run_pipeline(send_telegram=False)
    MockR.return_value.execute.assert_called_once()
    MockA.return_value.execute.assert_called_once()
    MockH.assert_called()
    MockC.assert_called()
    MockO.assert_called_once()
    MockRep.assert_called_once()
