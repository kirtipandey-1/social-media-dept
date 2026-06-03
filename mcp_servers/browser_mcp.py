"""
Local browser automation engine.
Persistent Playwright context — preserves login sessions without storing passwords.
Used by: Rick (Swipe), Borat (Radar), Dwight (Strategy/Uploads).
"""
import logging
import json
import time
from pathlib import Path
from config import load_settings
from db.sqlite_db import get_connection as get_db_connection

log = logging.getLogger("browser_mcp")

PROJECT_DIR = Path.home() / "social-media-dept"
SESSION_DIR = PROJECT_DIR / "config" / "browser_session"


def _launch_persistent_context(headful: bool = False):
    """Launch a persistent Playwright browser context."""
    from playwright.sync_api import sync_playwright
    SESSION_DIR.mkdir(parents=True, exist_ok=True)
    p = sync_playwright().__enter__()
    ctx = p.chromium.launch_persistent_context(
        user_data_dir=str(SESSION_DIR),
        headless=not headful,
        args=["--disable-blink-features=AutomationControlled"],
        ignore_default_args=["--enable-automation"],
    )
    return p, ctx


def get_unseen_saved_urls(candidate_urls: list) -> list:
    """Return only URLs not yet in saved_post_analysis table."""
    conn = get_db_connection()
    seen = {r[0] for r in conn.execute("SELECT post_url FROM saved_post_analysis").fetchall()}
    return [u for u in candidate_urls if u not in seen]


def mark_url_analyzed(url: str, collection: str, hook_text: str, visual_notes: str) -> None:
    """Record an analyzed saved post."""
    conn = get_db_connection()
    conn.execute("""
    INSERT OR REPLACE INTO saved_post_analysis
        (post_url, collection, hook_text, raw_insight)
    VALUES (?, ?, ?, ?)
    """, (url, collection, hook_text, visual_notes))
    conn.commit()


def log_upload_result(file_path: str, title: str, status: str, error: str = "") -> None:
    """Log YouTube upload result to upload_queue table."""
    conn = get_db_connection()
    conn.execute("""
    INSERT INTO upload_queue (file_path, title, status, uploaded_at, error_msg)
    VALUES (?, ?, ?, CURRENT_TIMESTAMP, ?)
    """, (file_path, title, status, error))
    conn.commit()


def _analyze_screenshot_with_vision(screenshot_bytes: bytes, url: str) -> dict:
    """Analyze a screenshot with Ollama llava."""
    try:
        import base64, ollama
        from mcp_servers.base_server import get_vision_model
        b64 = base64.b64encode(screenshot_bytes).decode()
        resp = ollama.chat(
            model=get_vision_model(),
            messages=[{"role": "user", "content": """Analyze this social media screenshot.
Return exactly:
HOOK: [on-screen text or opening hook]
STYLE: [visual editing style]
FORMAT: [talking head / b-roll / text overlay / etc]
TRIGGER: [curiosity / fear / inspiration / humor / etc]""", "images": [b64]}]
        )
        raw = resp.message.content
        result = {"hook": "", "visual_notes": raw}
        if "HOOK:" in raw:
            result["hook"] = raw.split("HOOK:")[1].split("\n")[0].strip()
        return result
    except Exception as e:
        log.warning("Vision analysis failed: %s", e)
        return {"hook": "", "visual_notes": ""}


def crawl_saved_collections() -> dict:
    """Crawl Instagram saved collections. Analyzes new posts with llava."""
    s = load_settings()
    collections = s.get("instagram_saved", {}).get("collections", ["content"])
    results = {"analyzed": 0, "skipped": 0, "errors": 0}
    try:
        p, ctx = _launch_persistent_context(headful=False)
        page = ctx.new_page()
        for collection in collections:
            try:
                page.goto("https://www.instagram.com/", wait_until="networkidle", timeout=30000)
                if "accounts/login" in page.url:
                    log.warning("Instagram session expired — run scripts/export_cookies.sh")
                    _send_session_expired_alert()
                    break
                page.goto("https://www.instagram.com/your_activity/saved/", timeout=20000)
                links = page.eval_on_selector_all("article a[href*='/p/']", "els => els.map(e=>e.href)")[:20]
                unseen = get_unseen_saved_urls(links)
                for url in unseen:
                    try:
                        page.goto(url, wait_until="networkidle", timeout=20000)
                        shot = page.screenshot()
                        analysis = _analyze_screenshot_with_vision(shot, url)
                        mark_url_analyzed(url, collection, analysis["hook"], analysis["visual_notes"])
                        results["analyzed"] += 1
                    except Exception as e:
                        log.error("Error on %s: %s", url, e)
                        results["errors"] += 1
                results["skipped"] += len(links) - len(unseen)
            except Exception as e:
                log.error("Collection '%s' failed: %s", collection, e)
                results["errors"] += 1
        ctx.close()
        p.__exit__(None, None, None)
    except Exception as e:
        log.error("Browser launch failed: %s", e)
        results["errors"] += 1
    return results


def _send_session_expired_alert() -> None:
    """Send Telegram alert when session expires."""
    try:
        from config import load_settings
        import asyncio, telegram
        s = load_settings()
        token = s.get("telegram", {}).get("bot_token", "")
        chat_id = s.get("telegram", {}).get("chat_id", "")
        if not token or not chat_id:
            return
        msg = "Instagram session expired. Run: `bash ~/social-media-dept/scripts/export_cookies.sh`"
        async def _send():
            bot = telegram.Bot(token=token)
            await bot.send_message(chat_id=chat_id, text=msg, parse_mode="Markdown")
        loop = asyncio.new_event_loop()
        loop.run_until_complete(_send())
        loop.close()
    except Exception:
        pass


def upload_and_schedule_video(file_path: str) -> dict:
    """Upload mp4 to YouTube Studio using persistent browser (headful)."""
    video = Path(file_path)
    meta_file = video.with_suffix(".json")
    if not video.exists():
        return {"status": "error", "message": f"File not found: {file_path}"}
    if not meta_file.exists():
        return {"status": "error", "message": f"Missing metadata: {meta_file}"}

    meta = json.loads(meta_file.read_text())
    title = meta.get("title", "Untitled")
    description = meta.get("description", "")
    publish_at = meta.get("publish_at", "")

    try:
        p, ctx = _launch_persistent_context(headful=True)
        page = ctx.new_page()
        page.goto("https://studio.youtube.com/", wait_until="networkidle", timeout=30000)
        if "accounts.google.com" in page.url:
            ctx.close(); p.__exit__(None, None, None)
            return {"status": "error", "message": "Google session expired — log in to YouTube Studio first"}

        page.click('button[aria-label="Create"]', timeout=10000)
        page.click('tp-yt-paper-item:has-text("Upload videos")', timeout=5000)
        page.locator('input[type="file"]').set_input_files(str(video))
        time.sleep(3)

        title_field = page.locator("#textbox").first
        title_field.click(); title_field.press("Control+a"); title_field.type(title)
        desc_field = page.locator("#textbox").nth(1)
        desc_field.click(); desc_field.type(description)

        for _ in range(3):
            page.click('button:has-text("Next")')
            time.sleep(1)

        if publish_at:
            page.click('tp-yt-paper-radio-button[name="SCHEDULE"]')
            page.fill('input[placeholder*="date"]', publish_at[:10])
            page.click('button:has-text("Schedule")')
        else:
            page.click('button:has-text("Save")')
        time.sleep(3)

        ctx.close(); p.__exit__(None, None, None)

        archive = PROJECT_DIR / "assets" / "archive"
        archive.mkdir(parents=True, exist_ok=True)
        video.rename(archive / video.name)
        meta_file.rename(archive / meta_file.name)

        log_upload_result(str(video), title, "success")
        return {"status": "success", "title": title}

    except Exception as e:
        log.error("Upload failed: %s", e)
        log_upload_result(str(video), title, "error", str(e))
        return {"status": "error", "message": str(e)}


try:
    from mcp.server.fastmcp import FastMCP
    mcp = FastMCP("browser-mcp")

    @mcp.tool()
    def crawl_saved_collections_tool() -> dict:
        """Crawl Instagram saved collections for new posts. Analyzes with llava vision."""
        return crawl_saved_collections()

    @mcp.tool()
    def upload_and_schedule_video_tool(file_path: str) -> dict:
        """Upload an mp4 from assets/ready_to_upload/ to YouTube Studio."""
        return upload_and_schedule_video(file_path)

    if __name__ == "__main__":
        mcp.run()

except ImportError:
    pass
