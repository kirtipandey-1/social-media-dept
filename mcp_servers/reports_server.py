"""Employee 3 — McLovin (Performance Analyst) MCP server."""
import logging
from db.sqlite_db import get_connection as get_db_connection
from mcp_servers.base_server import call_ollama, get_ollama_model

log = logging.getLogger("reports_server")


def _gather_daily_context(conn) -> str:
    trends = conn.execute("""
    SELECT topic, signal_strength FROM trends
    WHERE detected_at > datetime('now','-1 day') ORDER BY signal_strength DESC LIMIT 5
    """).fetchall()
    opps = conn.execute("""
    SELECT title, score FROM opportunities WHERE status='new' ORDER BY score DESC LIMIT 3
    """).fetchall()
    reddit = conn.execute("""
    SELECT title, upvotes FROM reddit_posts
    WHERE scraped_at > datetime('now','-1 day') ORDER BY upvotes DESC LIMIT 5
    """).fetchall()
    lines = ["## Today's Data\n"]
    if trends:
        lines.append("**Top Trends:**")
        for t in trends:
            lines.append(f"- {t[0]} (strength: {t[1]:.2f})" if t[1] else f"- {t[0]}")
    if opps:
        lines.append("\n**Opportunities:**")
        for o in opps:
            lines.append(f"- {o[0]} (score: {o[1]})")
    if reddit:
        lines.append("\n**Hot Reddit Posts:**")
        for r in reddit:
            lines.append(f"- {r[0]} ({r[1]} upvotes)")
    return "\n".join(lines)


def generate_daily_report() -> str:
    conn = get_db_connection()
    context = _gather_daily_context(conn)
    prompt = f"""You are McLovin, the Performance Analyst for a music producer.
Write a concise daily brief in Markdown based on this data:

{context}

Include: top trends, best hook opportunity, 1 specific action recommendation.
Keep it under 300 words. Use bullet points."""
    report = call_ollama(get_ollama_model(), prompt)
    conn.execute("""
    INSERT INTO reports (type, period_start, period_end, body_md)
    VALUES ('daily', datetime('now','-1 day'), datetime('now'), ?)
    """, (report,))
    conn.commit()
    return report


def generate_weekly_report() -> str:
    conn = get_db_connection()
    trends = conn.execute("""
    SELECT topic, COUNT(*) as freq FROM trends
    WHERE detected_at > datetime('now','-7 days')
    GROUP BY topic ORDER BY freq DESC LIMIT 10
    """).fetchall()
    posts = conn.execute("""
    SELECT title, upvotes, subreddit FROM reddit_posts
    WHERE scraped_at > datetime('now','-7 days') ORDER BY upvotes DESC LIMIT 10
    """).fetchall()
    context = "Week trends:\n" + "\n".join(f"- {t[0]} ({t[1]}x)" for t in trends)
    context += "\n\nTop Reddit:\n" + "\n".join(f"- {p[0]} ({p[1]} upvotes, r/{p[2]})" for p in posts)
    prompt = f"""Write a weekly social media review for a music producer in Markdown.
Data: {context}
Include: trend summary, competitor highlights, top pain points, 5 script ideas, strategic recommendations.
~500 words."""
    report = call_ollama(get_ollama_model(), prompt)
    conn.execute("""
    INSERT INTO reports (type, period_start, period_end, body_md)
    VALUES ('weekly', datetime('now','-7 days'), datetime('now'), ?)
    """, (report,))
    conn.commit()
    return report


def generate_monthly_report() -> str:
    conn = get_db_connection()
    prompt = "Write a monthly growth audit for a music producer. Focus on content strategy, opportunities, and audience growth. Use Markdown. ~600 words."
    report = call_ollama(get_ollama_model(), prompt)
    conn.execute("""
    INSERT INTO reports (type, period_start, period_end, body_md)
    VALUES ('monthly', datetime('now','-30 days'), datetime('now'), ?)
    """, (report,))
    conn.commit()
    return report


def get_report(report_type: str = "daily", date: str | None = None) -> str:
    conn = get_db_connection()
    if date:
        row = conn.execute("""
        SELECT body_md FROM reports WHERE type=? AND DATE(created_at)=? LIMIT 1
        """, (report_type, date)).fetchone()
    else:
        row = conn.execute("""
        SELECT body_md FROM reports WHERE type=? ORDER BY created_at DESC LIMIT 1
        """, (report_type,)).fetchone()
    return row[0] if row else f"No {report_type} report found."


try:
    from mcp.server.fastmcp import FastMCP
    mcp = FastMCP("reports-server")

    @mcp.tool()
    def generate_daily_report_tool() -> str:
        """McLovin: Generate today's daily brief."""
        return generate_daily_report()

    @mcp.tool()
    def generate_weekly_report_tool() -> str:
        """McLovin: Generate this week's performance review."""
        return generate_weekly_report()

    @mcp.tool()
    def generate_monthly_report_tool() -> str:
        """McLovin: Generate monthly growth audit."""
        return generate_monthly_report()

    @mcp.tool()
    def get_report_tool(type: str = "daily", date: str = "") -> str:
        """McLovin: Retrieve a saved report by type and optional date (YYYY-MM-DD)."""
        return get_report(type, date or None)

    if __name__ == "__main__":
        mcp.run()

except ImportError:
    pass
