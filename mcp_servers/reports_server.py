"""Employee 3 — McLovin (Performance Analyst) MCP server."""
import logging
from db.sqlite_db import get_connection as get_db_connection
from mcp_servers.base_server import call_ollama, get_ollama_model

log = logging.getLogger("reports_server")


def _gather_daily_context(conn) -> str:
    cur = conn.cursor()
    cur.execute("""
    SELECT topic, signal_strength FROM trends
    WHERE detected_at > NOW() - INTERVAL '1 day' ORDER BY signal_strength DESC LIMIT 5
    """)
    trends = cur.fetchall()
    cur.execute("""
    SELECT title, score FROM opportunities WHERE status='new' ORDER BY score DESC LIMIT 3
    """)
    opps = cur.fetchall()
    cur.execute("""
    SELECT title, upvotes FROM reddit_posts
    WHERE scraped_at > NOW() - INTERVAL '1 day' ORDER BY upvotes DESC LIMIT 5
    """)
    reddit = cur.fetchall()
    lines = ["## Today's Data\n"]
    if trends:
        lines.append("**Top Trends:**")
        for t in trends:
            lines.append(f"- {t['topic']} (strength: {t['signal_strength']:.2f})" if t['signal_strength'] else f"- {t['topic']}")
    if opps:
        lines.append("\n**Opportunities:**")
        for o in opps:
            lines.append(f"- {o['title']} (score: {o['score']})")
    if reddit:
        lines.append("\n**Hot Reddit Posts:**")
        for r in reddit:
            lines.append(f"- {r['title']} ({r['upvotes']} upvotes)")
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
    cur = conn.cursor()
    cur.execute("""
    INSERT INTO reports (type, period_start, period_end, body_md)
    VALUES ('daily', NOW() - INTERVAL '1 day', NOW(), %s)
    """, (report,))
    conn.commit()
    return report


def generate_weekly_report() -> str:
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
    SELECT topic, COUNT(*) as freq FROM trends
    WHERE detected_at > NOW() - INTERVAL '7 days'
    GROUP BY topic ORDER BY freq DESC LIMIT 10
    """)
    trends = cur.fetchall()
    cur.execute("""
    SELECT title, upvotes, subreddit FROM reddit_posts
    WHERE scraped_at > NOW() - INTERVAL '7 days' ORDER BY upvotes DESC LIMIT 10
    """)
    posts = cur.fetchall()
    context = "Week trends:\n" + "\n".join(f"- {t['topic']} ({t['freq']}x)" for t in trends)
    context += "\n\nTop Reddit:\n" + "\n".join(f"- {p['title']} ({p['upvotes']} upvotes, r/{p['subreddit']})" for p in posts)
    prompt = f"""Write a weekly social media review for a music producer in Markdown.
Data: {context}
Include: trend summary, competitor highlights, top pain points, 5 script ideas, strategic recommendations.
~500 words."""
    report = call_ollama(get_ollama_model(), prompt)
    cur.execute("""
    INSERT INTO reports (type, period_start, period_end, body_md)
    VALUES ('weekly', NOW() - INTERVAL '7 days', NOW(), %s)
    """, (report,))
    conn.commit()
    return report


def generate_monthly_report() -> str:
    conn = get_db_connection()
    cur = conn.cursor()
    prompt = "Write a monthly growth audit for a music producer. Focus on content strategy, opportunities, and audience growth. Use Markdown. ~600 words."
    report = call_ollama(get_ollama_model(), prompt)
    cur.execute("""
    INSERT INTO reports (type, period_start, period_end, body_md)
    VALUES ('monthly', NOW() - INTERVAL '30 days', NOW(), %s)
    """, (report,))
    conn.commit()
    return report


def get_report(report_type: str = "daily", date: str | None = None) -> str:
    conn = get_db_connection()
    cur = conn.cursor()
    if date:
        cur.execute("""
        SELECT body_md FROM reports WHERE type=%s AND DATE(created_at)=%s LIMIT 1
        """, (report_type, date))
    else:
        cur.execute("""
        SELECT body_md FROM reports WHERE type=%s ORDER BY created_at DESC LIMIT 1
        """, (report_type,))
    row = cur.fetchone()
    return row["body_md"] if row else f"No {report_type} report found."


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
