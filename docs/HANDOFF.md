# Social Media Dept — Handoff Doc
_Last updated: 2026-06-03_

---

## What This Project Is

A Streamlit dashboard at `~/social-media-dept` with 12 AI "employees" that do social media intelligence for a music producer (hip-hop/boom bap niche). Runs locally on Mac, deployed to Streamlit Cloud for viewing on phone/laptop.

**Live URL:** `social-media-dept-yogezrzchj9cxohyfu57yt.streamlit.app`
**GitHub:** `https://github.com/kirtipandey-1/social-media-dept` (public)
**Local:** `http://localhost:8501`

---

## Tech Stack

- **Python 3.11**, uv package manager, venv at `.venv/`
- **Streamlit** — dashboard UI (12 pages)
- **Supabase (Postgres)** — main database (FULLY MIGRATED from SQLite)
- **DuckDB** — local analytics only
- **ChromaDB** — vector DB for hooks
- **Ollama** — local AI (llama3.1:8b text, llava vision) — Mac only
- **Playwright** — Instagram scraping — Mac only
- **Telegram bot** — employee slash commands + Claude interface
- **launchd** — 3am automated pipeline
- **Streamlit Community Cloud** — public deployment

---

## Database

**Supabase is the source of truth.** SQLite is gone.

```
DSN: postgresql://postgres.nciyncaqqyzajptzpzjh:Kirt1r0ck5!@aws-1-us-east-1.pooler.supabase.com:5432/postgres
Project ref: nciyncaqqyzajptzpzjh
```

Stored in:
- `~/.streamlit/secrets.toml` (local, gitignored)
- Streamlit Cloud → App Settings → Secrets

`db/sqlite_db.py` now connects to Postgres via psycopg2 (same function signatures, just different backend).

---

## What Works Where

| Feature | Mac (localhost) | Streamlit Cloud (phone/laptop) |
|---|---|---|
| View all data | ✅ | ✅ |
| Data persists | ✅ | ✅ (Supabase) |
| Paste analytics sync | ✅ | ✅ |
| Generate hooks/briefs | ✅ (Ollama) | ❌ info msg shown |
| Run research scraper | ✅ | ❌ info msg shown |
| Instagram scraping | ✅ (Playwright+cookies) | ❌ |
| 3am auto-pipeline | ✅ (launchd) | — |
| Telegram commands | ✅ | — |

**Important:** The user said NO external APIs. All AI uses local Ollama only.

---

## Telegram

- Bot token: `8927304933:AAFC7R_1OJ4_q8wIEjkmUg00ekcGiM9Gex0`
- Approved chat_id: `8791558283`
- Stored in: `config/settings.toml` (gitignored), `~/.claude/channels/telegram/.env`
- Claude Code Telegram plugin handles the bot (not a separate process)
- Employee commands: `/chad`, `/peter`, `/mclovin`, `/karen`, `/borat`, `/dwight`, `/rick`, `/speed`, `/gollum`, `/keanu`, `/drake`, `/gandalf`, `/status`
- Logic in: `workers/telegram_bot.py`

---

## MCP Servers (Claude Code)

All 10 registered in `~/.claude/settings.json`:
`hooks`, `comments`, `radar`, `reports`, `content`, `swipe`, `opinion`, `strategy`, `learning`, `voice`

Each corresponds to one AI employee. Files at `mcp_servers/*_server.py`.
Venv python: `/Users/kirtipandey/social-media-dept/.venv/bin/python`
PYTHONPATH env set to project root in each registration.

---

## launchd Jobs (3am pipeline)

Installed at `~/Library/LaunchAgents/`:
- `com.socialdept.main` — daily pipeline (research, analysis, reports)
- `com.socialdept.weekly` — weekly report
- `com.socialdept.monthly` — monthly report
- `com.socialdept.telegram` — **unloaded** (conflicts with Claude plugin)

Check: `launchctl list | grep socialdept`
Logs: `/tmp/socialdept-main.log`, `/tmp/socialdept-main.err`

---

## Reddit Subreddits (configured in config/settings.toml)

WeAreTheMusicMakers, beatmakers, makinghiphop, hiphopheads, boom_bap, 90sHipHop, undergroundhiphop, Griselda, RocMarciano, vinyl, lofi, samplesfortheculture

Sorted by upvotes (top.rss?t=week), stored in `reddit_posts` table.

---

## Active Work Item (INCOMPLETE)

**Competitor Feed redesign** was in progress when session ended. The user wants:
- ~~Thumbnail image~~ → **REMOVE**
- ✅ On-screen text from the video (via llava analyzing og:image)
- ✅ Brief video description (via llava)
- ✅ Caption (already captured)
- ✅ Video length (scrape from page metadata)
- ✅ Top comments (scrape via Playwright)

**What's already done:**
- `parse_post_element()` in `workers/research_scraper.py` already has `video_text`, `video_description`, `video_length`, `top_comments` fields
- `save_competitor_posts()` already inserts these fields
- The scraping loop still uses the OLD llava prompt (returns `ai_analysis`, not structured video_text/description)

**What still needs doing:**
1. Update DB schema — add `video_text`, `video_description`, `video_length`, `top_comments` columns to `competitor_posts` in Supabase (run ALTER TABLE migration in `init_schema`)
2. Update the inner scraping loop in `scrape_competitor_profile` to:
   - Extract video length from `meta[property="video:duration"]`
   - Scrape top 3 comments via Playwright selectors
   - Use updated llava prompt that returns `ON-SCREEN TEXT:` and `DESCRIPTION:` separately
3. Update `get_competitor_posts()` in `dashboard/db_helpers.py` to SELECT the new columns
4. Update `dashboard/pages/2_research.py` tab1 to display new format (no thumbnail, show text/description/length/comments)

**The subagent was rejected mid-run** — none of the above changes landed. Start fresh on this task.

---

## Key Files

```
~/social-media-dept/
├── dashboard/
│   ├── app.py                  # Main Streamlit app (auto-inits DB)
│   ├── db_helpers.py           # All DB queries (Postgres, %s placeholders)
│   └── pages/
│       ├── 1_home.py           # Dwight's daily brief
│       ├── 2_research.py       # Chad — competitor feed + reddit
│       ├── 3_hooks.py          # Peter — hook generation
│       ├── 4_analytics.py      # McLovin — paste-text sync
│       ├── 5_comments.py       # Karen — comment analysis
│       └── 11_strategy.py      # Dwight — strategy brief
├── db/
│   ├── sqlite_db.py            # NOW POSTGRES (psycopg2, RealDictCursor)
│   └── duckdb_db.py            # Analytics only (local)
├── mcp_servers/
│   └── *_server.py             # One per employee
├── workers/
│   ├── research_scraper.py     # Reddit RSS + Instagram Playwright
│   ├── telegram_bot.py         # Standalone bot (not running, use Claude plugin)
│   └── analytics_ingest.py     # Paste-text → DuckDB
├── config/
│   └── settings.toml           # GITIGNORED — has bot token + DB settings
└── .streamlit/
    └── secrets.toml            # GITIGNORED — has Supabase DSN
```

---

## How to Run Locally

```bash
cd ~/social-media-dept
.venv/bin/python -m streamlit run dashboard/app.py
```

## How to Deploy

```bash
cd ~/social-media-dept
git add -A && git commit -m "..." && git push
# Streamlit Cloud auto-redeploys from main branch
```

## Environment

Supabase DSN must be available. Set via:
- Local: `.streamlit/secrets.toml` → `[supabase] dsn = "..."`
- Cloud: Streamlit Cloud secrets panel
- Or env var: `SUPABASE_DSN="..."`
