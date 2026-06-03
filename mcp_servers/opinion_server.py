"""Employee 10 — Speed (Opinion Miner) MCP server.
YO YO YO! Aggressive, unhinged, high-octane opinion content generator.
"""
import re
import logging
from db.sqlite_db import get_connection as get_db_connection
from mcp_servers.base_server import call_ollama, get_ollama_model

log = logging.getLogger("opinion_server")

SPEED_SYSTEM = """You are Speed, an aggressive, high-octane content strategist for a music producer.
Generate controversial, discussion-driving content ideas. Be bold, polarizing, and opinionated.
Think Twitter beef, heated Reddit threads, and viral "hot take" content.
Return ONLY a numbered list. No explanations. Be DIRECT."""


def _parse_list(raw: str) -> list:
    lines = raw.strip().split("\n")
    return [re.sub(r"^\d+[\.\)]\s*", "", l).strip() for l in lines if l.strip() and len(l.strip()) > 8]


def _save_topics(topics: list, topic_type: str, source: str = "speed") -> None:
    conn = get_db_connection()
    cur = conn.cursor()
    for t in topics:
        cur.execute("""
        INSERT INTO opinion_topics (topic, type, source, relevance_score)
        VALUES (%s, %s, %s, 0.5)
        ON CONFLICT DO NOTHING
        """, (t, topic_type, source))
    conn.commit()


def generate_questions(count: int = 25) -> list:
    """Generate discussion questions worth answering as content."""
    conn = get_db_connection()
    cur = conn.cursor()
    # Pull recent Reddit pain points as context
    try:
        cur.execute("""
        SELECT title FROM reddit_posts ORDER BY upvotes DESC LIMIT 10
        """)
        reddit = cur.fetchall()
    except Exception:
        reddit = []
    context = "\n".join(f"- {r['title']}" for r in reddit) or "music production, beatmaking, mixing"

    prompt = f"""Generate {count} SPECIFIC questions music producers are debating RIGHT NOW.
These should start arguments in comments. Examples of the energy:
- "Do you ACTUALLY need music theory to make beats?"
- "Is buying sample packs cheating or just smart?"

Recent Reddit discussions for context:
{context}

Generate {count} questions, numbered list only."""
    raw = call_ollama(get_ollama_model(), prompt, system=SPEED_SYSTEM)
    questions = _parse_list(raw)[:count]
    _save_topics(questions, "question", "speed")
    _log_activity("generate_questions", f"count={len(questions)}")
    return questions


def generate_hot_takes(count: int = 10) -> list:
    """Generate controversial hot takes for content."""
    prompt = f"""Generate {count} CONTROVERSIAL hot takes about music production and beatmaking.
These should make people angry OR nod aggressively. Polarizing opinions only.
Examples: "Mixing in headphones is FINE if you know what you're doing"
Numbered list only. Be LOUD."""
    raw = call_ollama(get_ollama_model(), prompt, system=SPEED_SYSTEM)
    takes = _parse_list(raw)[:count]
    _save_topics(takes, "hot_take", "speed")
    _log_activity("generate_hot_takes", f"count={len(takes)}")
    return takes


def generate_discussion_topics(count: int = 25) -> list:
    """Generate weekly discussion topics."""
    prompt = f"""Generate {count} discussion topics for a music producer's content calendar.
These should spark comment sections. Mix of: industry debates, workflow opinions, gear takes, culture commentary.
Numbered list only."""
    raw = call_ollama(get_ollama_model(), prompt, system=SPEED_SYSTEM)
    topics = _parse_list(raw)[:count]
    _save_topics(topics, "discussion", "speed")
    _log_activity("generate_discussion_topics")
    return topics


def generate_contrarian_angles(topic: str) -> list:
    """Generate contrarian angles on a specific topic."""
    prompt = f"""Take this topic and give me 5 CONTRARIAN angles that would get engagement:
Topic: "{topic}"
Make them spicy. Numbered list only."""
    raw = call_ollama(get_ollama_model(), prompt, system=SPEED_SYSTEM)
    return _parse_list(raw)[:5]


def rank_opinion_opportunities(limit: int = 10) -> list:
    """Return top opinion topics ranked by relevance score."""
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
    SELECT topic, type, source, relevance_score, generated_at
    FROM opinion_topics WHERE used=0
    ORDER BY relevance_score DESC, generated_at DESC LIMIT %s
    """, (limit,))
    return [dict(r) for r in cur.fetchall()]


def _log_activity(action: str, detail: str = "") -> None:
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("INSERT INTO employee_activity_log (employee,action,detail) VALUES (%s,%s,%s)",
                     ("Speed", action, detail))
        conn.commit()
    except Exception:
        pass


try:
    from mcp.server.fastmcp import FastMCP
    mcp = FastMCP("opinion-server")

    @mcp.tool()
    def generate_questions_tool(count: int = 25) -> list:
        """Speed: Generate discussion questions worth answering as content."""
        return generate_questions(count)

    @mcp.tool()
    def generate_hot_takes_tool(count: int = 10) -> list:
        """Speed: Generate controversial hot takes for engagement content."""
        return generate_hot_takes(count)

    @mcp.tool()
    def generate_discussion_topics_tool(count: int = 25) -> list:
        """Speed: Generate weekly discussion content topics."""
        return generate_discussion_topics(count)

    @mcp.tool()
    def generate_contrarian_angles_tool(topic: str) -> list:
        """Speed: Get contrarian angles on any topic."""
        return generate_contrarian_angles(topic)

    @mcp.tool()
    def rank_opinion_opportunities_tool(limit: int = 10) -> list:
        """Speed: Get top unused opinion topics ranked by relevance."""
        return rank_opinion_opportunities(limit)

    if __name__ == "__main__":
        mcp.run()

except ImportError:
    pass
