"""Research scraper worker — Reddit RSS + Instagram Playwright."""
import feedparser
import logging
from datetime import datetime
from time import mktime

log = logging.getLogger("research_scraper")


def fetch_reddit_rss(subreddit: str, limit: int = 25) -> list:
    """Fetch top posts from a subreddit via RSS, sorted by weekly top + upvotes."""
    import re as _re
    url = f"https://www.reddit.com/r/{subreddit}/top.rss?t=week&limit={limit}"
    headers = {"User-Agent": "social-media-dept/1.0 research-bot"}
    feed = feedparser.parse(url, request_headers=headers)
    posts = []
    for entry in feed.entries[:limit]:
        link = getattr(entry, "link", "")
        if "/comments/" in link:
            reddit_id = link.rstrip("/").split("/comments/")[-1].split("/")[0]
        else:
            reddit_id = getattr(entry, "id", link).split("/")[-1]

        pt = getattr(entry, "published_parsed", None)
        posted_at = datetime.fromtimestamp(mktime(pt)).isoformat() if pt else None

        # Parse upvotes from summary HTML: "1,234 points"
        summary = getattr(entry, "summary", "")
        upvotes = 0
        m = _re.search(r"([\d,]+)\s+point", summary)
        if m:
            upvotes = int(m.group(1).replace(",", ""))

        posts.append({
            "reddit_id": reddit_id,
            "subreddit": subreddit,
            "title": getattr(entry, "title", ""),
            "body": summary,
            "url": link,
            "upvotes": upvotes,
            "num_comments": 0,
            "posted_at": posted_at,
        })
    return posts


def save_reddit_posts(conn, posts: list) -> int:
    """Persist Reddit posts to SQLite. Returns count saved."""
    saved = 0
    for p in posts:
        try:
            conn.execute("""
            INSERT OR IGNORE INTO reddit_posts
                (reddit_id, subreddit, title, body, url, upvotes, num_comments, posted_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, [p["reddit_id"], p["subreddit"], p["title"], p["body"],
                  p["url"], p.get("upvotes", 0), p.get("num_comments", 0),
                  p.get("posted_at")])
            saved += 1
        except Exception as e:
            log.warning("Skip reddit post %s: %s", p.get("reddit_id"), e)
    conn.commit()
    return saved


import re
from pathlib import Path
from playwright.sync_api import sync_playwright

COOKIES_PATH = Path.home() / "social-media-dept" / "config" / "cookies" / "instagram.json"


def parse_post_element(el: dict) -> dict:
    """Parse a dict of raw scraped values into normalised post data."""
    def to_int(v):
        if not v:
            return 0
        v = str(v).replace(",", "").replace(" ", "")
        m = re.match(r"([\d.]+)([KkMm]?)", v)
        if not m:
            return 0
        n, suffix = float(m.group(1)), m.group(2).upper()
        return int(n * {"K": 1000, "M": 1_000_000}.get(suffix, 1))

    return {
        "post_url": el.get("url", ""),
        "caption": el.get("caption", ""),
        "views": to_int(el.get("views", 0)),
        "likes": to_int(el.get("likes", 0)),
        "comments": to_int(el.get("comments", 0)),
        "saves": to_int(el.get("saves", 0)),
    }


from workers.base_worker import BaseWorker
from config import load_settings
from db.sqlite_db import get_connection


def save_competitor_posts(conn, handle: str, posts: list) -> int:
    """Persist competitor posts. Returns count saved."""
    row = conn.execute(
        "SELECT id FROM competitors WHERE handle=?", (handle,)
    ).fetchone()
    if not row:
        log.warning("Competitor @%s not in DB, skipping", handle)
        return 0
    competitor_id = row[0]
    saved = 0
    for p in posts:
        try:
            conn.execute("""
            INSERT OR IGNORE INTO competitor_posts
                (competitor_id, post_url, caption, views, likes, comments, saves)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """, [competitor_id, p["post_url"], p.get("caption", ""),
                  p.get("views", 0), p.get("likes", 0),
                  p.get("comments", 0), p.get("saves", 0)])
            saved += 1
        except Exception as e:
            log.warning("Skip post %s: %s", p.get("post_url"), e)
    conn.commit()
    return saved


def scrape_competitor_profile(handle: str, limit: int = 12) -> list:
    """Scrape public posts from a competitor Instagram profile via Playwright."""
    posts = []
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        ctx_kwargs = {}
        if COOKIES_PATH.exists():
            ctx_kwargs["storage_state"] = str(COOKIES_PATH)
        ctx = browser.new_context(**ctx_kwargs)
        page = ctx.new_page()
        try:
            page.goto(
                f"https://www.instagram.com/{handle}/",
                wait_until="networkidle",
                timeout=30000
            )
            # Detect cookie expiry (redirect to login)
            if "accounts/login" in page.url:
                raise RuntimeError(
                    f"Instagram session expired. Run scripts/export_cookies.sh"
                )
            links = page.eval_on_selector_all(
                "main a[href*='/p/'], main a[href*='/reel/']",
                "els => [...new Set(els.map(e => e.href.split('?')[0]))]"
            )[:limit]
            if not links:
                log.warning(
                    "No post/reel links found for @%s (selector may need updating or session is limited)",
                    handle,
                )

            for url in links:
                try:
                    page.goto(url, wait_until="networkidle", timeout=20000)
                    caption_el = page.query_selector(
                        "h1, [data-testid='post-comment-root'] span"
                    )
                    caption = caption_el.inner_text() if caption_el else ""
                    posts.append(parse_post_element({"url": url, "caption": caption}))
                except Exception as e:
                    log.warning("Error scraping %s: %s", url, e)
        finally:
            browser.close()
    return posts


class ResearchScraper(BaseWorker):
    name = "research_scraper"

    def run(self) -> str:
        s = load_settings()
        conn = get_connection()
        total_reddit = 0
        for sub in s.get("reddit", {}).get("subreddits", []):
            try:
                posts = fetch_reddit_rss(sub)
                n = save_reddit_posts(conn, posts)
                total_reddit += n
                log.info("Reddit r/%s: %d posts saved", sub, n)
            except Exception as e:
                log.error("Reddit r/%s failed: %s", sub, e)

        total_ig = 0
        for handle in s.get("competitors", {}).get("instagram", []):
            try:
                posts = scrape_competitor_profile(handle)
                n = save_competitor_posts(conn, handle, posts)
                total_ig += n
                log.info("Instagram @%s: %d posts saved", handle, n)
            except Exception as e:
                log.error("Instagram @%s failed: %s", handle, e)

        return f"Reddit:{total_reddit} Instagram:{total_ig}"


if __name__ == "__main__":
    ResearchScraper().execute()
