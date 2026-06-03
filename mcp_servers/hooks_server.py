"""Employee 2 — Head of Hooks MCP server."""
import re
import logging
from db.chroma_db import get_collection, upsert_hook, search_hooks

log = logging.getLogger("hooks_server")

HOOKS_SYSTEM = """You are a viral social media hook writer for music producers and beatmakers.
Generate short, punchy hook lines for short-form video content.
Each hook should be 5-12 words, create curiosity or address pain points.
Return ONLY a numbered list, one hook per line. No explanations."""


def get_hooks_collection():
    return get_collection()


def call_ollama(model: str, prompt: str, system: str | None = None) -> str:
    from mcp_servers.base_server import call_ollama as _call
    return _call(model, prompt, system)


def get_ollama_model() -> str:
    from mcp_servers.base_server import get_ollama_model as _get
    return _get()


def generate_hooks(topic: str, count: int = 25, save: bool = True) -> list:
    prompt = f"Generate {count} hooks for a short-form video about: {topic}\nFormat: numbered list only."
    raw = call_ollama(get_ollama_model(), prompt, system=HOOKS_SYSTEM)
    hooks = _parse_numbered_list(raw)[:count]
    if save and hooks:
        col = get_hooks_collection()
        for h in hooks:
            upsert_hook(col, h, category=_classify_hook(h), source="generated")
    log.info("Generated %d hooks for topic: %s", len(hooks), topic)
    return hooks


def _parse_numbered_list(text: str) -> list:
    lines = text.strip().split("\n")
    hooks = []
    for line in lines:
        clean = re.sub(r"^\d+[\.\)]\s*", "", line).strip()
        if clean and len(clean) > 5:
            hooks.append(clean)
    return hooks


def _classify_hook(text: str) -> str:
    t = text.lower()
    if any(w in t for w in ["nobody", "secret", "truth", "lies", "told"]):
        return "curiosity"
    if any(w in t for w in ["stop", "mistake", "wrong", "don't", "never"]):
        return "pain_point"
    if any(w in t for w in ["i made", "i earned", "my beat", "sold"]):
        return "flex"
    if any(w in t for w in ["challenge", "try", "dare", "bet"]):
        return "challenge"
    return "pattern_interrupt"


def search_hooks_fn(query: str, limit: int = 10) -> list:
    col = get_hooks_collection()
    return search_hooks(col, query, limit=limit)


def get_top_hooks(category: str | None = None, limit: int = 10) -> list:
    col = get_hooks_collection()
    kwargs = {"include": ["documents", "metadatas"]}
    if category:
        kwargs["where"] = {"category": category}
    results = col.get(**kwargs)
    hooks = []
    for i, doc in enumerate(results.get("documents") or []):
        meta = (results.get("metadatas") or [{}])[i]
        hooks.append({
            "hook": doc,
            "category": meta.get("category"),
            "score": meta.get("engagement_score", 0),
            "status": meta.get("status", "testing"),
        })
    hooks.sort(key=lambda x: x["score"], reverse=True)
    return hooks[:limit]


def save_hook_fn(text: str, category: str = "general", source: str = "manual") -> dict:
    col = get_hooks_collection()
    doc_id = upsert_hook(col, text, category=category, source=source)
    return {"id": doc_id, "saved": True}


def cluster_hooks() -> str:
    col = get_hooks_collection()
    if col.count() < 5:
        return "Not enough hooks to cluster (need at least 5)."
    all_hooks = col.get(include=["documents", "metadatas"])
    categories: dict = {}
    for doc, meta in zip(all_hooks["documents"], all_hooks["metadatas"]):
        cat = meta.get("category", "unknown")
        categories.setdefault(cat, []).append(doc)
    lines = ["## Hook Pattern Analysis\n"]
    for cat, hooks in sorted(categories.items(), key=lambda x: -len(x[1])):
        lines.append(f"**{cat}** ({len(hooks)} hooks)")
        for h in hooks[:3]:
            lines.append(f"  - {h}")
    return "\n".join(lines)


# ─── MCP Server registration ──────────────────────────────────────────────────
try:
    from mcp.server.fastmcp import FastMCP
    mcp = FastMCP("hooks-server")

    @mcp.tool()
    def generate_hooks_tool(topic: str, count: int = 25) -> list:
        """Generate hook ideas for a given topic."""
        return generate_hooks(topic, count)

    @mcp.tool()
    def search_hooks_tool(query: str, limit: int = 10) -> list:
        """Semantic search across hook database."""
        return search_hooks_fn(query, limit)

    @mcp.tool()
    def get_top_hooks_tool(category: str = "", limit: int = 10) -> list:
        """Get highest-scoring hooks, optionally filtered by category."""
        return get_top_hooks(category or None, limit)

    @mcp.tool()
    def save_hook_tool(text: str, category: str = "general", source: str = "manual") -> dict:
        """Save a hook to the database."""
        return save_hook_fn(text, category, source)

    @mcp.tool()
    def cluster_hooks_tool() -> str:
        """Run clustering analysis on all hooks."""
        return cluster_hooks()

    if __name__ == "__main__":
        mcp.run()

except ImportError:
    pass  # MCP not available — server functions still usable as plain Python
