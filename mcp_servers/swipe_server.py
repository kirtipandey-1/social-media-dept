"""Employee 9 — Rick (Swipe File Curator) MCP server.
Never gonna give up a good reference. Never gonna let it drop.
"""
import logging
from db.sqlite_db import get_connection as get_db_connection
from mcp_servers.base_server import call_ollama, get_ollama_model

log = logging.getLogger("swipe_server")


def add_swipe_entry(
    source_url: str,
    platform: str = "instagram",
    collection: str = "content",
    hook_text: str = "",
    topic: str = "",
    creator_handle: str = "",
    content_format: str = "",
    emotional_trigger: str = "",
    narrative_style: str = "",
    personal_rating: int = 0,
    notes: str = "",
) -> dict:
    """Add a piece of content to the swipe file."""
    conn = get_db_connection()
    conn.execute("""
    INSERT OR REPLACE INTO swipe_file
        (source_url, platform, collection, hook_text, topic, creator_handle,
         content_format, emotional_trigger, narrative_style, personal_rating, notes)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, [source_url, platform, collection, hook_text, topic, creator_handle,
          content_format, emotional_trigger, narrative_style, personal_rating, notes])
    conn.commit()
    _log_activity("add_swipe_entry", source_url)
    return {"saved": True, "source_url": source_url}


def search_swipe_file(query: str, limit: int = 10) -> list:
    """Text search across swipe file entries."""
    conn = get_db_connection()
    like = f"%{query}%"
    rows = conn.execute("""
    SELECT source_url, platform, hook_text, topic, creator_handle,
           content_format, emotional_trigger, personal_rating, notes
    FROM swipe_file
    WHERE hook_text LIKE ? OR topic LIKE ? OR creator_handle LIKE ?
       OR content_format LIKE ? OR notes LIKE ?
    ORDER BY personal_rating DESC, date_saved DESC
    LIMIT ?
    """, [like, like, like, like, like, limit]).fetchall()
    return [dict(r) for r in rows]


def get_similar_saved_content(topic: str, limit: int = 5) -> list:
    """Find saved content similar to a given topic."""
    return search_swipe_file(topic, limit)


def get_top_saved_patterns(limit: int = 10) -> list:
    """Get most common formats, triggers, and topics in the swipe file."""
    conn = get_db_connection()
    formats = conn.execute("""
    SELECT content_format, COUNT(*) as count FROM swipe_file
    WHERE content_format != '' GROUP BY content_format ORDER BY count DESC LIMIT ?
    """, (limit,)).fetchall()
    triggers = conn.execute("""
    SELECT emotional_trigger, COUNT(*) as count FROM swipe_file
    WHERE emotional_trigger != '' GROUP BY emotional_trigger ORDER BY count DESC LIMIT ?
    """, (limit,)).fetchall()
    topics = conn.execute("""
    SELECT topic, COUNT(*) as count FROM swipe_file
    WHERE topic != '' GROUP BY topic ORDER BY count DESC LIMIT ?
    """, (limit,)).fetchall()
    return {
        "top_formats": [{"format": r[0], "count": r[1]} for r in formats],
        "top_triggers": [{"trigger": r[0], "count": r[1]} for r in triggers],
        "top_topics": [{"topic": r[0], "count": r[1]} for r in topics],
    }


def get_favorite_creators(limit: int = 10) -> list:
    """Get most-saved creators from swipe file."""
    conn = get_db_connection()
    rows = conn.execute("""
    SELECT creator_handle, COUNT(*) as saves, AVG(personal_rating) as avg_rating
    FROM swipe_file WHERE creator_handle != ''
    GROUP BY creator_handle ORDER BY saves DESC, avg_rating DESC LIMIT ?
    """, (limit,)).fetchall()
    return [{"creator": r[0], "saves": r[1], "avg_rating": round(r[2] or 0, 1)} for r in rows]


def get_favorite_hook_types(limit: int = 10) -> list:
    """Get most-saved hook patterns."""
    conn = get_db_connection()
    rows = conn.execute("""
    SELECT hook_text, personal_rating, platform, creator_handle
    FROM swipe_file WHERE hook_text != ''
    ORDER BY personal_rating DESC, date_saved DESC LIMIT ?
    """, (limit,)).fetchall()
    return [dict(r) for r in rows]


def generate_weekly_taste_report() -> str:
    """Generate Rick's weekly taste report — formats, topics, hooks, creators."""
    patterns = get_top_saved_patterns()
    creators = get_favorite_creators(5)
    hooks = get_favorite_hook_types(5)

    context = f"""Swipe file analysis:
Top formats: {patterns.get('top_formats', [])}
Top triggers: {patterns.get('top_triggers', [])}
Top topics: {patterns.get('top_topics', [])}
Top creators: {creators}
Top hooks: {[h.get('hook_text','') for h in hooks]}"""

    prompt = f"""You are Rick, the Swipe File Curator. Write a weekly taste report for a music producer.
Analyze what content they've been saving and extract strategic insights.

{context}

Format as Markdown. Cover: emerging format preferences, hook patterns, creator influences, content angles to explore.
~300 words."""
    report = call_ollama(get_ollama_model(), prompt)
    _log_activity("weekly_taste_report", "generated")
    return report


def _log_activity(action: str, detail: str = "") -> None:
    try:
        conn = get_db_connection()
        conn.execute("INSERT INTO employee_activity_log (employee,action,detail) VALUES (?,?,?)",
                     ("Rick", action, detail))
        conn.commit()
    except Exception:
        pass


try:
    from mcp.server.fastmcp import FastMCP
    mcp = FastMCP("swipe-server")

    @mcp.tool()
    def add_swipe_entry_tool(source_url: str, platform: str = "instagram",
                             hook_text: str = "", topic: str = "",
                             creator_handle: str = "", content_format: str = "",
                             emotional_trigger: str = "", personal_rating: int = 0,
                             notes: str = "") -> dict:
        """Rick: Add content to the swipe file taste database."""
        return add_swipe_entry(source_url, platform, hook_text=hook_text,
                               topic=topic, creator_handle=creator_handle,
                               content_format=content_format,
                               emotional_trigger=emotional_trigger,
                               personal_rating=personal_rating, notes=notes)

    @mcp.tool()
    def search_swipe_file_tool(query: str, limit: int = 10) -> list:
        """Rick: Search saved content by keyword."""
        return search_swipe_file(query, limit)

    @mcp.tool()
    def get_similar_saved_content_tool(topic: str, limit: int = 5) -> list:
        """Rick: Find saved content similar to a topic."""
        return get_similar_saved_content(topic, limit)

    @mcp.tool()
    def get_top_saved_patterns_tool() -> dict:
        """Rick: Get top formats, triggers, and topics from swipe file."""
        return get_top_saved_patterns()

    @mcp.tool()
    def get_favorite_creators_tool(limit: int = 10) -> list:
        """Rick: Get most-saved creators."""
        return get_favorite_creators(limit)

    @mcp.tool()
    def get_favorite_hook_types_tool(limit: int = 10) -> list:
        """Rick: Get highest-rated hook patterns."""
        return get_favorite_hook_types(limit)

    @mcp.tool()
    def weekly_taste_report_tool() -> str:
        """Rick: Generate weekly taste evolution report."""
        return generate_weekly_taste_report()

    if __name__ == "__main__":
        mcp.run()

except ImportError:
    pass
