#!/bin/bash
set -e

PROJECT_DIR="$HOME/social-media-dept"

echo ""
echo "╔══════════════════════════════════════════════════╗"
echo "║  🎵 Social Media Dept — Installation Script     ║"
echo "║     12 AI Employees | All Local | All Free      ║"
echo "╚══════════════════════════════════════════════════╝"
echo ""

# ─── 1. Homebrew ──────────────────────────────────────────────────────────────
if ! command -v brew &>/dev/null; then
  echo "Installing Homebrew..."
  /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
fi
echo "✓ Homebrew"

# ─── 2. UV ────────────────────────────────────────────────────────────────────
if ! command -v uv &>/dev/null; then
  echo "Installing UV..."
  curl -LsSf https://astral.sh/uv/install.sh | sh
  export PATH="$HOME/.local/bin:$PATH"
fi
echo "✓ UV"

# ─── 3. Python venv + dependencies ───────────────────────────────────────────
cd "$PROJECT_DIR"
echo "Creating Python 3.11 venv..."
uv venv .venv --python 3.11
echo "Installing Python dependencies..."
uv pip install -e .
echo "✓ Python dependencies"

# ─── 4. Playwright ────────────────────────────────────────────────────────────
echo "Installing Playwright Chromium..."
uv run playwright install chromium
echo "✓ Playwright Chromium"

# ─── 5. Whisper (installed separately — uv packaging issue on macOS 26) ───────
echo "Installing OpenAI Whisper (via pip)..."
"$PROJECT_DIR/.venv/bin/pip" install openai-whisper --quiet 2>/dev/null || \
  echo "  ⚠  Whisper install failed — voice features will use CLI fallback"
echo "✓ Whisper (voice transcription)"

# ─── 6. Ollama ────────────────────────────────────────────────────────────────
if ! command -v ollama &>/dev/null; then
  echo "Installing Ollama..."
  brew install ollama
fi
if ! ollama list &>/dev/null 2>&1; then
  echo "Starting Ollama service..."
  brew services start ollama
  sleep 5
fi
echo "Pulling Ollama models (this takes a few minutes the first time)..."
ollama pull llama3.1:8b
ollama pull llava
echo "✓ Ollama models ready (llama3.1:8b + llava)"

# ─── 7. Config ────────────────────────────────────────────────────────────────
if [ ! -f "$PROJECT_DIR/config/settings.toml" ]; then
  cp "$PROJECT_DIR/config/settings.toml.example" "$PROJECT_DIR/config/settings.toml"
fi
mkdir -p "$PROJECT_DIR/config/cookies"
mkdir -p "$PROJECT_DIR/config/browser_session"
mkdir -p "$PROJECT_DIR/assets/ready_to_upload"
mkdir -p "$PROJECT_DIR/assets/archive"
echo "✓ Config and asset directories"

# ─── 8. Telegram BotFather walkthrough ───────────────────────────────────────
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📱 TELEGRAM SETUP"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "Step 1: Open Telegram → search for @BotFather"
echo "Step 2: Send:  /newbot"
echo "Step 3: Name your bot (e.g. 'My Social Dept')"
echo "Step 4: Username (e.g. 'mysocialdept_bot')"
echo "Step 5: Copy the token BotFather gives you"
echo ""
read -p "Paste your Telegram bot token (or press Enter to skip): " BOT_TOKEN
if [ -n "$BOT_TOKEN" ]; then
  echo ""
  echo "Step 6: Send any message to your bot in Telegram"
  echo "Step 7: Visit this URL in your browser:"
  echo "        https://api.telegram.org/bot${BOT_TOKEN}/getUpdates"
  echo "        Look for 'id' inside 'chat' in the JSON"
  echo ""
  read -p "Paste your chat_id: " CHAT_ID
  if [ -n "$CHAT_ID" ]; then
    sed -i '' "s/bot_token = \"\"/bot_token = \"${BOT_TOKEN}\"/" "$PROJECT_DIR/config/settings.toml"
    sed -i '' "s/chat_id   = \"\"/chat_id   = \"${CHAT_ID}\"/" "$PROJECT_DIR/config/settings.toml"
    echo "✓ Telegram configured"
  fi
else
  echo "  (Skipped — edit config/settings.toml later to add your bot token)"
fi

# ─── 9. Database init ─────────────────────────────────────────────────────────
echo ""
echo "Initialising databases..."
cd "$PROJECT_DIR" && uv run python scripts/init_db.py
echo "✓ Databases initialised"

# ─── 10. launchd scheduling ──────────────────────────────────────────────────
echo ""
echo "Installing scheduled jobs (pipeline runs at 3am)..."
bash "$PROJECT_DIR/scripts/load_launchd.sh"
echo "✓ launchd agents active"

# ─── 11. Cookie export helper ────────────────────────────────────────────────
cat > "$PROJECT_DIR/scripts/export_cookies.sh" << 'COOKIESCRIPT'
#!/bin/bash
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🍪 INSTAGRAM SESSION COOKIE REFRESH"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "Your Instagram session has expired. To refresh:"
echo ""
echo "1. Install 'Cookie-Editor' Chrome extension"
echo "   https://chromewebstore.google.com/detail/cookie-editor/hlkenndednhfkekhgcdicdfddnkalmdm"
echo ""
echo "2. Go to https://instagram.com and log in"
echo ""
echo "3. Click Cookie-Editor → Export → Export as JSON"
echo ""
echo "4. Save to: ~/social-media-dept/config/cookies/instagram.json"
echo ""
echo "The overnight pipeline will resume automatically."
COOKIESCRIPT
chmod +x "$PROJECT_DIR/scripts/export_cookies.sh"
echo "✓ Cookie export helper created"

# ─── 12. Claude Code MCP config ──────────────────────────────────────────────
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🤖 CLAUDE CODE MCP SETUP"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "To give Claude Code direct access to all 12 employees:"
echo ""
echo "  Open Claude Code settings → MCP Servers → Add"
echo "  Or merge this file into your claude_desktop_config.json:"
echo ""
echo "  $PROJECT_DIR/.claude/mcp_servers/config.json"
echo ""

# ─── 13. Start dashboard ─────────────────────────────────────────────────────
echo ""
echo "╔══════════════════════════════════════════════════╗"
echo "║  ✅ Installation Complete!                       ║"
echo "║                                                  ║"
echo "║  Start dashboard:                                ║"
echo "║  cd ~/social-media-dept                          ║"
echo "║  uv run streamlit run dashboard/app.py \\         ║"
echo "║    --server.address=0.0.0.0 --port=8501          ║"
echo "║                                                  ║"
echo "║  Pipeline runs automatically at 3am.            ║"
echo "║  Telegram reports sent when configured.         ║"
echo "╚══════════════════════════════════════════════════╝"
echo ""
