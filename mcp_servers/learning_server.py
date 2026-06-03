"""Employee 12 — Gandalf (Swipe File Learning Engine) MCP server.
You shall not drop a bad hook.
Analyzes WHY content is being saved. Feeds Speed, Dwight, and Keanu.
"""
import logging
from db.sqlite_db import get_connection as get_db_connection
from mcp_servers.base_server import call_ollama, get_ollama_model

log = logging.getLogger("learning_server")

GANDALF_SYSTEM = """You are Gandalf, the Swipe File Learning Engine.
You speak slowly, with deep authority, treating saved social media links like ancient runes.
Analyze patterns with wisdom. Find the deep WHY behind what content is being saved.
Speak in flowing paragraphs. Be philosophical but actionable."""

TASTE_CATEGORIES = [
    "Nostalgia", "Producer Psychology", "Music Industry", "Storytelling",
    "Humor", "Contrarian Takes", "Hip-Hop History", "Sampling",
    "Career Advice", "Creative Process", "Personal Branding", "Technical Skills"
]


def cluster_saved_content() -> dict:
    """Cluster saved content into thematic categories."""
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
    SELECT source_url, hook_text, topic, emotional_trigger, content_format, notes
    FROM swipe_file ORDER BY date_saved DESC LIMIT 100
    """)
    swipes = cur.fetchall()

    if not swipes:
        return {"analysis": "The swipe file is empty. Rick must gather content first.", "clusters": {}}

    content_summary = "\n".join(
        f"- [{r['topic'] or 'unknown topic'}] {r['hook_text'] or ''} | trigger:{r['emotional_trigger'] or '?'} | format:{r['content_format'] or '?'}"
        for r in swipes[:50]
    )

    prompt = f"""Analyze this saved content collection from a music producer.
Cluster it into these categories: {', '.join(TASTE_CATEGORIES)}

Content:
{content_summary}

For each category found, briefly describe what it reveals about the creator's taste.
Return as structured analysis. Be wise and specific."""

    analysis = call_ollama(get_ollama_model(), prompt, system=GANDALF_SYSTEM)

    # Build simple cluster counts from DB
    clusters = {}
    for cat in TASTE_CATEGORIES:
        cat_lower = cat.lower()
        cur.execute("""
        SELECT COUNT(*) AS n FROM swipe_file
        WHERE LOWER(topic) LIKE %s OR LOWER(notes) LIKE %s OR LOWER(hook_text) LIKE %s
        """, (f"%{cat_lower}%", f"%{cat_lower}%", f"%{cat_lower}%"))
        count = cur.fetchone()["n"]
        if count > 0:
            clusters[cat] = count

    _log_activity("cluster_saved_content", f"{len(swipes)} items analyzed")
    return {"analysis": analysis, "clusters": clusters}


def get_taste_evolution() -> str:
    """Analyze how creator taste is evolving over time."""
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
    SELECT topic, emotional_trigger, content_format FROM swipe_file
    WHERE date_saved > NOW() - INTERVAL '30 days'
    ORDER BY date_saved DESC LIMIT 30
    """)
    recent = cur.fetchall()
    cur.execute("""
    SELECT topic, emotional_trigger, content_format FROM swipe_file
    WHERE date_saved <= NOW() - INTERVAL '30 days'
    ORDER BY date_saved DESC LIMIT 30
    """)
    older = cur.fetchall()

    recent_topics = [r["topic"] for r in recent if r["topic"]]
    older_topics = [r["topic"] for r in older if r["topic"]]

    prompt = f"""Analyze the evolution of a music producer's taste over time.

Last 30 days saved content topics: {recent_topics[:20]}
Older saved content topics: {older_topics[:20]}

What is changing? What themes are emerging? What does this reveal about their creative direction?
Be wise, specific, and prophetic."""

    analysis = call_ollama(get_ollama_model(), prompt, system=GANDALF_SYSTEM)
    _log_activity("get_taste_evolution")
    return analysis


def generate_learning_report() -> str:
    """Full monthly learning report fed to Speed, Dwight, and Keanu."""
    cluster_data = cluster_saved_content()
    evolution = get_taste_evolution()

    prompt = f"""Synthesize this creative intelligence into a monthly learning report.

Cluster Analysis:
{cluster_data.get('analysis', '')}

Taste Evolution:
{evolution}

Generate a strategic report covering:
1. Dominant creative themes (what they're obsessed with)
2. Emerging interests (new patterns in the last 30 days)
3. Content angles to explore (based on what they save)
4. Hook patterns from their swipe file
5. Recommendations for Speed (opinion topics), Dwight (strategy), Keanu (creative direction)

Format as Markdown. ~500 words."""

    report = call_ollama(get_ollama_model(), prompt, system=GANDALF_SYSTEM)
    _log_activity("generate_learning_report", "fed to Speed+Dwight+Keanu")
    return report


def _log_activity(action: str, detail: str = "") -> None:
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("INSERT INTO employee_activity_log (employee,action,detail) VALUES (%s,%s,%s)",
                     ("Gandalf", action, detail))
        conn.commit()
    except Exception:
        pass


try:
    from mcp.server.fastmcp import FastMCP
    mcp = FastMCP("learning-server")

    @mcp.tool()
    def cluster_saved_content_tool() -> dict:
        """Gandalf: Cluster saved content by theme — discover WHY it's being saved."""
        return cluster_saved_content()

    @mcp.tool()
    def get_taste_evolution_tool() -> str:
        """Gandalf: Analyze how creator taste is evolving over time."""
        return get_taste_evolution()

    @mcp.tool()
    def generate_learning_report_tool() -> str:
        """Gandalf: Full monthly learning report fed to Speed, Dwight, and Keanu."""
        return generate_learning_report()

    if __name__ == "__main__":
        mcp.run()

except ImportError:
    pass
