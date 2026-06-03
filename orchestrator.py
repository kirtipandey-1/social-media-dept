#!/usr/bin/env python3
"""Main pipeline orchestrator. Called by launchd at 3am.
Routes: Chad→Peter→Speed, Rick→Peter+Speed, Karen→Speed, McLovin+Peter+Borat→Dwight
"""
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

log = logging.getLogger("orchestrator")
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    handlers=[
        logging.FileHandler("/tmp/social-media-dept.log"),
        logging.StreamHandler(),
    ]
)


def _log_routing(source: str, target: str, detail: str = "") -> None:
    try:
        from db.sqlite_db import get_connection
        conn = get_connection()
        conn.execute(
            "INSERT INTO employee_activity_log (employee, action, detail) VALUES (?,?,?)",
            (source, f"→ {target}", detail)
        )
        conn.commit()
    except Exception:
        pass


def run_pipeline(send_telegram: bool = True) -> None:
    log.info("=== Social Media Dept Pipeline Starting (12 Employees) ===")

    # Phase 1: Data collection
    log.info("--- Chad (Research) scraping ---")
    from workers.research_scraper import ResearchScraper
    try:
        result = ResearchScraper().execute()
        _log_routing("Chad", "Peter+Speed", result)
    except Exception as e:
        log.error("Chad scrape failed: %s", e)

    log.info("--- Analytics ingest ---")
    from workers.analytics_ingest import AnalyticsIngest
    try:
        AnalyticsIngest().execute()
    except Exception as e:
        log.error("Analytics ingest failed: %s", e)

    # Phase 2: AI intelligence layer
    from db.sqlite_db import get_connection
    conn = get_connection()

    log.info("--- Karen (Comments) analyzing ---")
    from mcp_servers.comments_server import analyze_comments
    unanalyzed = conn.execute(
        "SELECT DISTINCT post_url FROM comments WHERE analyzed_at IS NULL LIMIT 20"
    ).fetchall()
    urls = [row[0] for row in unanalyzed] or ["latest"]
    for url in urls:
        try:
            analyze_comments(url)
        except Exception as e:
            log.error("Karen failed for %s: %s", url, e)
    _log_routing("Karen", "Speed")

    log.info("--- Peter (Hooks) generating ---")
    from mcp_servers.hooks_server import generate_hooks
    recent_trends = conn.execute(
        "SELECT topic FROM trends ORDER BY detected_at DESC LIMIT 3"
    ).fetchall()
    topics = [t[0] for t in recent_trends] or ["music production", "beatmaking", "mixing"]
    for topic in topics:
        try:
            generate_hooks(topic, count=10)
            _log_routing("Peter", "Dwight", f"hooks for: {topic}")
        except Exception as e:
            log.error("Peter hook gen failed for %s: %s", topic, e)

    log.info("--- Borat (Radar) scanning ---")
    from mcp_servers.radar_server import scan_opportunities
    try:
        result = scan_opportunities()
        log.info("Borat: %s", result)
        _log_routing("Borat", "Dwight", str(result))
    except Exception as e:
        log.error("Borat scan failed: %s", e)

    log.info("--- McLovin (Reports) generating ---")
    from mcp_servers.reports_server import generate_daily_report
    try:
        generate_daily_report()
        _log_routing("McLovin", "Dwight", "daily report ready")
    except Exception as e:
        log.error("McLovin report failed: %s", e)

    # Phase 3: Notify
    if send_telegram:
        log.info("--- Telegram notify ---")
        from workers.notifier import TelegramNotifier
        try:
            TelegramNotifier("daily").execute()
        except Exception as e:
            log.error("Telegram failed: %s", e)

    log.info("=== Pipeline Complete ===")


if __name__ == "__main__":
    run_pipeline()
