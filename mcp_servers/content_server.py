"""Employee 6 — Head of Content MCP server."""
import logging
import re
from db.sqlite_db import get_connection as get_db_connection
from mcp_servers.base_server import call_ollama, get_ollama_model

log = logging.getLogger("content_server")

SCRIPT_SYSTEM = """You are a content strategist for a music producer making short-form video.
Write talking head video scripts. Be conversational, direct, and punchy.
Always use this EXACT format with these EXACT labels:
HOOK: [5-12 word opening line]
PROBLEM: [2 sentences describing the pain point in the audience's words]
INSIGHT: [3-4 sentences with your unique take or solution]
CTA: [1 sentence call to action]"""

NICHE_SUBREDDITS = {
    "beatmaking": ["beatmakers", "makinghiphop", "WeAreTheMusicMakers"],
    "dj": ["DJs", "edmproduction"],
    "production": ["WeAreTheMusicMakers", "edmproduction", "ableton"],
}


def get_pain_points(niche: str = "beatmaking", limit: int = 10) -> list:
    conn = get_db_connection()
    relevant = NICHE_SUBREDDITS.get(niche.lower(), [])
    if relevant:
        placeholders = ",".join("?" * len(relevant))
        rows = conn.execute(f"""
        SELECT title, body, subreddit, upvotes, url
        FROM reddit_posts
        WHERE upvotes > 5 AND subreddit IN ({placeholders})
        ORDER BY upvotes DESC, scraped_at DESC
        LIMIT ?
        """, (*relevant, limit * 3)).fetchall()
    else:
        rows = conn.execute("""
        SELECT title, body, subreddit, upvotes, url
        FROM reddit_posts WHERE upvotes > 5
        ORDER BY upvotes DESC, scraped_at DESC LIMIT ?
        """, (limit * 3,)).fetchall()
    return [{"title": r[0], "body": r[1], "subreddit": r[2],
             "upvotes": r[3], "url": r[4]} for r in rows][:limit]


def generate_script(pain_point: str, duration_seconds: int = 60) -> dict:
    word_count = duration_seconds * 2
    prompt = f"""Write a {duration_seconds}-second talking head script (~{word_count} words).
Pain point: "{pain_point}"
The creator is a music producer/beatmaker giving advice to other producers."""
    raw = call_ollama(get_ollama_model(), prompt, system=SCRIPT_SYSTEM)
    script = _parse_script(raw)
    _save_script(pain_point, script)
    return script


def _parse_script(raw: str) -> dict:
    result = {"hook": "", "problem": "", "insight": "", "cta": ""}
    for key in result:
        m = re.search(
            rf"{key.upper()}:\s*(.+?)(?=\n[A-Z]+:|$)",
            raw, re.DOTALL | re.IGNORECASE
        )
        if m:
            result[key] = m.group(1).strip()
    return result


def _save_script(pain_point: str, script: dict) -> None:
    try:
        conn = get_db_connection()
        conn.execute("""
        INSERT INTO scripts (pain_point, hook, problem, insight, cta)
        VALUES (?, ?, ?, ?, ?)
        """, [pain_point, script.get("hook", ""), script.get("problem", ""),
              script.get("insight", ""), script.get("cta", "")])
        conn.commit()
    except Exception as e:
        log.warning("Could not save script: %s", e)


def get_script_ideas(count: int = 5) -> list:
    points = get_pain_points(limit=count)
    return [{"idea": p["title"], "source": p["subreddit"],
             "upvotes": p["upvotes"]} for p in points]


def get_saved_scripts(limit: int = 20) -> list:
    conn = get_db_connection()
    rows = conn.execute("""
    SELECT id, pain_point, hook, problem, insight, cta, generated_at
    FROM scripts ORDER BY generated_at DESC LIMIT ?
    """, (limit,)).fetchall()
    return [dict(r) for r in rows]


try:
    from mcp.server.fastmcp import FastMCP
    mcp = FastMCP("content-server")

    @mcp.tool()
    def get_pain_points_tool(niche: str = "beatmaking", limit: int = 10) -> list:
        """Get top pain points from Reddit for script ideas."""
        return get_pain_points(niche, limit)

    @mcp.tool()
    def generate_script_tool(pain_point: str, duration_seconds: int = 60) -> dict:
        """Generate a talking head video script from a pain point."""
        return generate_script(pain_point, duration_seconds)

    @mcp.tool()
    def get_script_ideas_tool(count: int = 5) -> list:
        """Get script ideas ranked by Reddit engagement."""
        return get_script_ideas(count)

    @mcp.tool()
    def get_saved_scripts_tool(limit: int = 20) -> list:
        """Retrieve previously generated scripts."""
        return get_saved_scripts(limit)

    if __name__ == "__main__":
        mcp.run()

except ImportError:
    pass
