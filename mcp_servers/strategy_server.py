"""Employee 11 — Dwight (Content Strategist) MCP server.
Bears. Beets. Battlestar Galactica. Executive intelligence layer.
Consumes ALL employee outputs. Produces the Daily Brief.
"""
import logging
from db.sqlite_db import get_connection as get_db_connection
from mcp_servers.base_server import call_ollama, get_ollama_model

log = logging.getLogger("strategy_server")

DWIGHT_SYSTEM = """You are Dwight, the Content Strategist for a music producer's social media department.
You are intense, rigid, authoritative, and strictly logical.
Your job is to synthesize intelligence from 11 other AI employees into one actionable daily brief.
Be specific, prioritized, and direct. No fluff. Every recommendation must have a reason."""


def _gather_all_intelligence(conn) -> str:
    """Aggregate data from all employees for the brief."""
    sections = []

    # Chad (Research): recent trends + competitor posts
    trends = conn.execute("""
    SELECT topic, signal_strength FROM trends
    ORDER BY detected_at DESC LIMIT 5
    """).fetchall()
    if trends:
        sections.append("TRENDS (Chad): " + ", ".join(f"{t[0]}({t[1] or 0:.1f})" for t in trends))

    comp_posts = conn.execute("""
    SELECT c.handle, cp.views FROM competitor_posts cp
    JOIN competitors c ON cp.competitor_id=c.id
    ORDER BY cp.scraped_at DESC LIMIT 3
    """).fetchall()
    if comp_posts:
        sections.append("COMPETITORS (Chad): " + ", ".join(f"@{p[0]} {p[1] or 0} views" for p in comp_posts))

    # Peter (Hooks): top hooks
    top_hooks = conn.execute("""
    SELECT title FROM reddit_posts ORDER BY upvotes DESC LIMIT 3
    """).fetchall()
    if top_hooks:
        sections.append("HOT TOPICS (Peter): " + " | ".join(h[0][:60] for h in top_hooks))

    # McLovin (Reports): recent performance
    latest_report = conn.execute("""
    SELECT body_md FROM reports WHERE type='daily' ORDER BY created_at DESC LIMIT 1
    """).fetchone()
    if latest_report:
        sections.append(f"PERFORMANCE (McLovin): {latest_report[0][:300]}...")

    # Karen (Comments): pain points
    pain_points = conn.execute("""
    SELECT insight FROM comment_insights WHERE category='pain_point'
    ORDER BY frequency DESC LIMIT 3
    """).fetchall()
    if pain_points:
        sections.append("AUDIENCE PAIN (Karen): " + " | ".join(p[0] for p in pain_points))

    # Borat (Radar): opportunities
    opps = conn.execute("""
    SELECT title, score FROM opportunities WHERE status='new'
    ORDER BY score DESC LIMIT 3
    """).fetchall()
    if opps:
        sections.append("OPPORTUNITIES (Borat): " + " | ".join(f"{o[0]}({o[1]})" for o in opps))

    # Rick (Swipe): top patterns
    top_formats = conn.execute("""
    SELECT content_format, COUNT(*) as c FROM swipe_file
    WHERE content_format != '' GROUP BY content_format ORDER BY c DESC LIMIT 2
    """).fetchall()
    if top_formats:
        sections.append("SWIPE PATTERNS (Rick): " + " | ".join(f[0] for f in top_formats))

    # Speed (Opinion): top questions
    questions = conn.execute("""
    SELECT topic FROM opinion_topics WHERE type='question' AND used=0
    ORDER BY relevance_score DESC LIMIT 3
    """).fetchall()
    if questions:
        sections.append("HOT QUESTIONS (Speed): " + " | ".join(q[0][:60] for q in questions))

    return "\n".join(sections) if sections else "No data yet — run research first."


def generate_daily_brief() -> str:
    """Generate Dwight's executive Daily Brief consuming all employee outputs."""
    conn = get_db_connection()
    intelligence = _gather_all_intelligence(conn)

    prompt = f"""Generate the Daily Brief for a music producer/beatmaker's social media strategy.

Intelligence from all departments:
{intelligence}

Structure the brief with these EXACT sections:
## Dwight's Daily Brief

**Recommended Post Today:** [specific content idea with hook]
**Top Opportunities:** [2-3 bullet points]
**Questions Worth Answering:** [2 discussion questions]
**Competitor Alert:** [1 notable competitor move]
**Hook Recommendations:** [2-3 hook ideas]
**Performance Note:** [1 key metric observation]
**Emerging Opportunity:** [1 trend to act on this week]

Be SPECIFIC. Every point must be actionable. ~400 words."""

    brief = call_ollama(get_ollama_model(), prompt, system=DWIGHT_SYSTEM)

    # Save to daily_briefs table
    conn.execute("INSERT INTO daily_briefs (body_md) VALUES (?)", (brief,))
    conn.commit()
    _log_routing_event()
    return brief


def get_latest_brief() -> str:
    """Get the most recent Daily Brief."""
    conn = get_db_connection()
    row = conn.execute("""
    SELECT body_md FROM daily_briefs ORDER BY created_at DESC LIMIT 1
    """).fetchone()
    return row[0] if row else "No brief generated yet. Run generate_daily_brief()."


def watch_upload_queue() -> dict:
    """Check assets/ready_to_upload/ for new video files and trigger uploads."""
    from pathlib import Path
    watch_dir = Path.home() / "social-media-dept" / "assets" / "ready_to_upload"
    watch_dir.mkdir(parents=True, exist_ok=True)
    mp4_files = list(watch_dir.glob("*.mp4"))
    results = {"queued": len(mp4_files), "files": []}
    for f in mp4_files:
        meta = f.with_suffix(".json")
        if meta.exists():
            results["files"].append({"video": str(f), "metadata": str(meta)})
        else:
            results["files"].append({"video": str(f), "metadata": "MISSING — create .json sidecar"})
    return results


def _log_routing_event() -> None:
    try:
        conn = get_db_connection()
        conn.execute("INSERT INTO employee_activity_log (employee,action,detail) VALUES (?,?,?)",
                     ("Dwight", "generate_daily_brief", "consumed: Chad+Peter+McLovin+Karen+Borat+Rick+Speed"))
        conn.commit()
    except Exception:
        pass


try:
    from mcp.server.fastmcp import FastMCP
    mcp = FastMCP("strategy-server")

    @mcp.tool()
    def generate_daily_brief_tool() -> str:
        """Dwight: Generate the executive Daily Brief from all employee intelligence."""
        return generate_daily_brief()

    @mcp.tool()
    def get_latest_brief_tool() -> str:
        """Dwight: Get the most recent Daily Brief."""
        return get_latest_brief()

    @mcp.tool()
    def watch_upload_queue_tool() -> dict:
        """Dwight: Check assets/ready_to_upload/ for videos ready to publish."""
        return watch_upload_queue()

    if __name__ == "__main__":
        mcp.run()

except ImportError:
    pass
