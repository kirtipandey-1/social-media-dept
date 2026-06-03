"""
Local Voice Interaction Layer.
All 12 employees speak with distinct macOS say voices.
Whisper transcribes locally (offline). No cloud APIs.
"""
import os
import re
import subprocess
import logging
from pathlib import Path
from config import load_settings

log = logging.getLogger("voice_server")

PROJECT_DIR = Path.home() / "social-media-dept"
AUDIO_PATH = str(PROJECT_DIR / "db" / "voice_query.wav")

# Intent keyword routing
INTENT_PATTERNS = {
    "brief":        ["brief", "today", "summary", "what's up", "daily", "dwight"],
    "hooks":        ["hook", "hooks", "generate hook", "peter", "ideas"],
    "script":       ["script", "write a script", "talking head", "gollum"],
    "opportunities":["opportunity", "opportunities", "radar", "borat", "trends"],
    "swipe":        ["swipe", "saved", "rick", "collection"],
    "questions":    ["question", "hot take", "opinion", "speed", "debate"],
    "report":       ["report", "performance", "analytics", "mclovin"],
    "research":     ["research", "competitors", "chad", "reddit"],
    "learning":     ["learning", "taste", "gandalf", "cluster"],
    "strategy":     ["strategy", "plan", "dwight"],
}


def strip_markdown(text: str) -> str:
    """Remove markdown formatting for speech output."""
    text = re.sub(r"\*\*(.+?)\*\*", r"\1", text)   # bold
    text = re.sub(r"\*(.+?)\*", r"\1", text)          # italic
    text = re.sub(r"#{1,6}\s*", "", text)              # headers
    text = re.sub(r"`{1,3}[^`]*`{1,3}", "", text)     # code
    text = re.sub(r"\[([^\]]+)\]\([^\)]+\)", r"\1", text)  # links
    text = re.sub(r"^\s*[-•]\s*", "", text, flags=re.MULTILINE)  # bullets
    text = re.sub(r"\n{3,}", "\n\n", text)             # excess newlines
    return text.strip()


def get_employee_voice(employee_name: str) -> str:
    """Look up the macOS say voice for an employee from settings.toml."""
    try:
        s = load_settings()
        employees = s.get("employees", {})
        for key, cfg in employees.items():
            if cfg.get("name", "").lower() == employee_name.lower():
                return cfg.get("voice", "Samantha")
    except Exception:
        pass
    return "Samantha"


def speak_as_employee(text: str, voice_name: str = "Samantha", employee: str = "") -> None:
    """Strip markdown and speak text using macOS say command."""
    if employee:
        voice_name = get_employee_voice(employee)
    clean = strip_markdown(text)
    # Truncate for speech (say is slow for very long text)
    if len(clean) > 600:
        clean = clean[:597] + "..."
    try:
        subprocess.run(["say", "-v", voice_name, clean], check=False, timeout=60)
    except Exception as e:
        log.warning("say command failed: %s", e)


def record_local_mic(duration: int = 6, sample_rate: int = 16000) -> bool:
    """Record from microphone. Returns True on success."""
    try:
        import sounddevice as sd
        import soundfile as sf
        Path(AUDIO_PATH).parent.mkdir(parents=True, exist_ok=True)
        log.info("Recording %ds at %dHz...", duration, sample_rate)
        recording = sd.rec(int(duration * sample_rate), samplerate=sample_rate, channels=1)
        sd.wait()
        sf.write(AUDIO_PATH, recording, sample_rate)
        return True
    except Exception as e:
        log.error("Recording failed: %s", e)
        return False


def transcribe_local_audio(audio_path: str | None = None) -> str:
    """Transcribe WAV file using local Whisper. Falls back to CLI subprocess."""
    path = audio_path or AUDIO_PATH
    if not os.path.exists(path):
        return ""

    # Try Python import first
    try:
        import whisper
        s = load_settings()
        model_name = s.get("voice", {}).get("whisper_model", "base")
        model = whisper.load_model(model_name)
        result = model.transcribe(path)
        return result.get("text", "").strip()
    except ImportError:
        pass  # whisper not importable, try CLI

    # Fall back to whisper CLI subprocess
    try:
        result = subprocess.run(
            ["whisper", path, "--model", "base", "--output_format", "txt",
             "--output_dir", str(Path(path).parent)],
            capture_output=True, text=True, timeout=120
        )
        txt_path = Path(path).with_suffix(".txt")
        if txt_path.exists():
            text = txt_path.read_text().strip()
            txt_path.unlink()
            return text
    except Exception as e:
        log.warning("Whisper CLI failed: %s", e)

    return ""


# ── Intent routing ────────────────────────────────────────────────────────────

def _get_daily_brief() -> str:
    from mcp_servers.strategy_server import get_latest_brief
    return get_latest_brief()

def _generate_hooks(topic: str, count: int = 10) -> list:
    from mcp_servers.hooks_server import generate_hooks
    return generate_hooks(topic, count)

def _generate_script(pain_point: str) -> dict:
    from mcp_servers.content_server import generate_script
    return generate_script(pain_point, 60)

def _get_opportunities() -> list:
    from mcp_servers.radar_server import get_alerts
    return get_alerts()

def _get_questions() -> list:
    from mcp_servers.opinion_server import generate_questions
    return generate_questions(5)

def _get_report() -> str:
    from mcp_servers.reports_server import get_report
    return get_report("daily")


def route_intent(query: str) -> str:
    """Route a transcribed query to the appropriate employee and return response text."""
    q = query.lower().strip()
    if not q:
        return "I didn't catch that. Try again."

    # Detect intent
    detected = None
    for intent, keywords in INTENT_PATTERNS.items():
        if any(kw in q for kw in keywords):
            detected = intent
            break

    log.info("Intent detected: %s for query: %s", detected, q)

    try:
        if detected == "brief":
            speak_as_employee("Dwight here. Commencing Daily Brief retrieval. Stand by.", employee="Dwight")
            brief = _get_daily_brief()
            return brief

        elif detected == "hooks":
            # Extract topic from query
            topic = q.replace("generate", "").replace("hooks", "").replace("hook", "").replace("some", "").strip()
            if not topic or len(topic) < 3:
                topic = "beatmaking"
            speak_as_employee(f"Peter here! I am PUMPED to generate hooks about {topic}! Let's GO!", employee="Peter")
            hooks = _generate_hooks(topic, count=5)
            return "\n".join(f"{i+1}. {h}" for i, h in enumerate(hooks))

        elif detected == "script":
            pain_point = q.replace("write a script", "").replace("script", "").replace("about", "").strip()
            if not pain_point or len(pain_point) < 5:
                pain_point = "music production struggles"
            speak_as_employee("My precious script... Gollum is crafting it...", employee="Gollum")
            script = _generate_script(pain_point)
            return f"HOOK: {script['hook']}\n\nPROBLEM: {script['problem']}\n\nINSIGHT: {script['insight']}\n\nCTA: {script['cta']}"

        elif detected == "opportunities":
            speak_as_employee("VERY NICE! Borat is checking the radar!", employee="Borat")
            opps = _get_opportunities()
            if opps:
                return "\n".join(f"- {o['title']} (score: {o['score']})" for o in opps[:3])
            return "No new opportunities detected. The radar is quiet."

        elif detected == "questions":
            speak_as_employee("YO YO YO! Speed here! I got your questions!", employee="Speed")
            questions = _get_questions()
            return "\n".join(f"{i+1}. {q}" for i, q in enumerate(questions[:5]))

        elif detected == "report":
            speak_as_employee("McLovin here! Pulling the performance report now!", employee="McLovin")
            return _get_report()

        else:
            speak_as_employee("Query acknowledged. The database is stable.", voice_name="Samantha")
            return f"I heard: {query}. Try asking about your brief, hooks, scripts, opportunities, or reports."

    except Exception as e:
        log.error("Intent routing failed: %s", e)
        return f"Something went wrong: {e}"


def handle_voice_interaction() -> dict:
    """Full voice pipeline: record → transcribe → route → speak response."""
    s = load_settings()
    voice_cfg = s.get("voice", {})
    duration = voice_cfg.get("record_seconds", 6)
    sample_rate = voice_cfg.get("sample_rate", 16000)

    speak_as_employee("Listening...", voice_name="Samantha")

    if not record_local_mic(duration=duration, sample_rate=sample_rate):
        return {"error": "Recording failed"}

    query = transcribe_local_audio()
    if not query:
        speak_as_employee("Could not transcribe. Please try again.", voice_name="Samantha")
        return {"error": "Transcription failed", "audio_path": AUDIO_PATH}

    log.info("Transcribed: %s", query)
    response = route_intent(query)
    speak_as_employee(response, voice_name=voice_cfg.get("default_voice", "Samantha"))

    return {"query": query, "response": response}


try:
    from mcp.server.fastmcp import FastMCP
    mcp = FastMCP("voice-server")

    @mcp.tool()
    def handle_voice_interaction_tool() -> dict:
        """Record mic, transcribe with Whisper, route to employee, speak response."""
        return handle_voice_interaction()

    @mcp.tool()
    def speak_tool(text: str, employee: str = "") -> None:
        """Speak text as a specific employee using macOS say."""
        speak_as_employee(text, employee=employee)

    @mcp.tool()
    def route_intent_tool(query: str) -> str:
        """Route a text query to the appropriate employee and return response."""
        return route_intent(query)

    if __name__ == "__main__":
        mcp.run()

except ImportError:
    pass
