"""Analytics ingest worker — parses Instagram/YouTube/Facebook insights into DuckDB."""
import re
import logging
from pathlib import Path
from workers.base_worker import BaseWorker
from db.duckdb_db import get_connection, init_schema, upsert_post_performance

log = logging.getLogger("analytics_ingest")


def parse_insights_text(text: str) -> dict:
    """Parse a text block from Instagram/YouTube Insights into a metrics dict."""
    def extract(label):
        m = re.search(rf"{label}[:\s]+([\d,]+)", text, re.IGNORECASE)
        return int(m.group(1).replace(",", "")) if m else 0

    return {
        "views":    extract("views"),
        "likes":    extract("likes"),
        "saves":    extract("saves"),
        "comments": extract("comments"),
        "reach":    extract("reach"),
        "shares":   extract("shares"),
    }


class AnalyticsIngest(BaseWorker):
    name = "analytics_ingest"

    def run(self) -> str:
        conn = get_connection()
        init_schema(conn)
        log.info(
            "Analytics ingest ready. Platforms: instagram, youtube, facebook. "
            "Use 'Sync Analytics' in dashboard or ask Claude Code."
        )
        return "ok — interactive sync via dashboard or Claude Code"


if __name__ == "__main__":
    AnalyticsIngest().execute()
