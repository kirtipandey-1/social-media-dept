"""Employee 8 — Borat (Opportunity Radar) MCP server."""
import re
import logging
from db.sqlite_db import get_connection as get_db_connection
from mcp_servers.base_server import call_ollama, get_ollama_model
from config import load_settings

log = logging.getLogger("radar_server")


def score_topic(topic: str) -> int:
    prompt = f"""Score this topic for a music producer/beatmaker (0-100).
Topic: "{topic}"
Consider: trending potential, niche relevance (hip-hop, beats, mixing, production).
First line MUST be: "Score: [number]" """
    raw = call_ollama(get_ollama_model(), prompt)
    m = re.search(r"[Ss]core:\s*(\d+)", raw)
    return min(100, max(0, int(m.group(1)))) if m else 50


def scan_opportunities() -> dict:
    conn = get_db_connection()
    cur = conn.cursor()
    s = load_settings()
    threshold = s.get("thresholds", {}).get("opportunity_alert_score", 75)
    cur.execute("""
    SELECT topic, source, signal_strength FROM trends
    WHERE detected_at > NOW() - INTERVAL '7 days'
    ORDER BY signal_strength DESC LIMIT 20
    """)
    trends = cur.fetchall()
    found = 0
    for trend in trends:
        cur.execute(
            "SELECT id FROM opportunities WHERE title=%s AND status='new'",
            (trend["topic"],)
        )
        existing = cur.fetchone()
        if existing:
            continue
        sc = score_topic(trend["topic"])
        if sc >= threshold:
            cur.execute("""
            INSERT INTO opportunities (type, title, score, notes, status)
            VALUES ('trend', %s, %s, %s, 'new')
            """, (trend["topic"], sc, f"Source: {trend['source']}"))
            found += 1
    conn.commit()
    _log_activity("scan_opportunities", f"found={found}")
    return {"opportunities_found": found, "trends_checked": len(trends)}


def get_alerts() -> list:
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
    SELECT id, type, title, score, notes, source_url
    FROM opportunities WHERE status='new'
    ORDER BY score DESC LIMIT 10
    """)
    return [dict(r) for r in cur.fetchall()]


def get_rising_creators(niche: str = "beatmaking") -> str:
    return ("Very nice! Rising creator detection requires the browser engine. "
            "Run: from mcp_servers.browser_mcp import scan_rising_creators")


def analyze_saved_collections() -> str:
    return ("Very nice! Saved collection analysis uses the browser engine. "
            "Run: from mcp_servers.browser_mcp import crawl_saved_collections")


def _log_activity(action: str, detail: str = "") -> None:
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO employee_activity_log (employee, action, detail) VALUES (%s,%s,%s)",
            ("Borat", action, detail)
        )
        conn.commit()
    except Exception:
        pass


try:
    from mcp.server.fastmcp import FastMCP
    mcp = FastMCP("radar-server")

    @mcp.tool()
    def scan_opportunities_tool() -> dict:
        """Borat: Score current trends and surface high-value opportunities. VERY NICE!"""
        return scan_opportunities()

    @mcp.tool()
    def get_alerts_tool() -> list:
        """Borat: Get unread high-score opportunities."""
        return get_alerts()

    @mcp.tool()
    def score_topic_tool(topic: str) -> int:
        """Borat: Rate a topic 0-100 for your niche."""
        return score_topic(topic)

    @mcp.tool()
    def get_rising_creators_tool(niche: str = "beatmaking") -> str:
        """Borat: Find fast-growing creators (uses browser engine)."""
        return get_rising_creators(niche)

    @mcp.tool()
    def analyze_saved_collections_tool() -> str:
        """Borat: Analyze saved Instagram collections (uses browser engine)."""
        return analyze_saved_collections()

    if __name__ == "__main__":
        mcp.run()

except ImportError:
    pass
