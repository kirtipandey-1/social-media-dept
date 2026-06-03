"""Employee 7 — Karen (Comment Intelligence Agent) MCP server."""
import json
import logging
import re
from db.sqlite_db import get_connection as get_db_connection
from mcp_servers.base_server import call_ollama, get_ollama_model

log = logging.getLogger("comments_server")

CLASSIFY_SYSTEM = """Classify this social media comment.
Return ONLY valid JSON with no extra text:
{"category": "pain_point|faq|praise|request|other", "sentiment": "positive|negative|neutral"}"""


def classify_comment(text: str) -> dict:
    raw = call_ollama(get_ollama_model(), text, system=CLASSIFY_SYSTEM)
    try:
        m = re.search(r"\{[^}]+\}", raw)
        return json.loads(m.group()) if m else {"category": "other", "sentiment": "neutral"}
    except Exception:
        return {"category": "other", "sentiment": "neutral"}


def analyze_comments(post_url: str) -> dict:
    conn = get_db_connection()
    rows = conn.execute("""
    SELECT id, body FROM comments
    WHERE post_url=? AND analyzed_at IS NULL
    LIMIT 50
    """, (post_url,)).fetchall()
    counts = {"pain_point": 0, "faq": 0, "praise": 0, "request": 0, "other": 0}
    for row in rows:
        result = classify_comment(row["body"])
        cat = result.get("category", "other")
        sent = result.get("sentiment", "neutral")
        conn.execute("""
        UPDATE comments SET category=?, sentiment=?, analyzed_at=CURRENT_TIMESTAMP
        WHERE id=?
        """, (cat, sent, row["id"]))
        counts[cat] = counts.get(cat, 0) + 1
    conn.commit()
    return {"analyzed": len(rows), "breakdown": counts}


def get_pain_points(limit: int = 10) -> list:
    conn = get_db_connection()
    rows = conn.execute("""
    SELECT insight, frequency, example_comment, generated_at
    FROM comment_insights WHERE category='pain_point'
    ORDER BY frequency DESC LIMIT ?
    """, (limit,)).fetchall()
    return [dict(r) for r in rows]


def get_content_requests() -> list:
    conn = get_db_connection()
    rows = conn.execute("""
    SELECT body FROM comments WHERE category='request'
    ORDER BY scraped_at DESC LIMIT 20
    """).fetchall()
    return [{"request": r[0]} for r in rows]


def get_audience_language() -> list:
    conn = get_db_connection()
    rows = conn.execute("""
    SELECT body FROM comments ORDER BY scraped_at DESC LIMIT 100
    """).fetchall()
    if not rows:
        return []
    all_text = " ".join(r[0] for r in rows)
    prompt = f"""Extract 20 specific phrases that music producers use when talking about problems.
Return a numbered list of exact phrases from this text:
{all_text[:3000]}"""
    raw = call_ollama(get_ollama_model(), prompt)
    return [re.sub(r"^\d+[\.\)]\s*", "", l).strip()
            for l in raw.split("\n") if l.strip() and len(l.strip()) > 5][:20]


def _log_activity(action: str, detail: str = "") -> None:
    try:
        conn = get_db_connection()
        conn.execute(
            "INSERT INTO employee_activity_log (employee, action, detail) VALUES (?,?,?)",
            ("Karen", action, detail)
        )
        conn.commit()
    except Exception:
        pass


try:
    from mcp.server.fastmcp import FastMCP
    mcp = FastMCP("comments-server")

    @mcp.tool()
    def analyze_comments_tool(post_url: str) -> dict:
        """Karen: Classify unanalyzed comments for a post."""
        _log_activity("analyze_comments", post_url)
        return analyze_comments(post_url)

    @mcp.tool()
    def get_pain_points_tool(limit: int = 10) -> list:
        """Karen: Get top recurring audience pain points."""
        return get_pain_points(limit)

    @mcp.tool()
    def get_content_requests_tool() -> list:
        """Karen: Get what your audience is asking you to make."""
        return get_content_requests()

    @mcp.tool()
    def get_audience_language_tool() -> list:
        """Karen: Extract verbatim phrases your audience uses."""
        return get_audience_language()

    if __name__ == "__main__":
        mcp.run()

except ImportError:
    pass
