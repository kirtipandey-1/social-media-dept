from unittest.mock import patch, MagicMock
import subprocess


def test_strip_markdown_removes_formatting():
    from mcp_servers.voice_server import strip_markdown
    text = "**Hello** world! ## Title\n- bullet *italic*"
    result = strip_markdown(text)
    assert "**" not in result
    assert "##" not in result
    assert "*" not in result
    assert "Hello" in result


def test_speak_as_employee_calls_say(monkeypatch):
    from mcp_servers.voice_server import speak_as_employee
    calls = []
    monkeypatch.setattr(subprocess, "run", lambda cmd, **kw: calls.append(cmd))
    speak_as_employee("Hello world", voice_name="Samantha")
    assert any("say" in str(c) for c in calls)
    assert any("Samantha" in str(c) for c in calls)


def test_route_intent_brief(monkeypatch):
    from mcp_servers.voice_server import route_intent
    called = {}

    def mock_brief():
        called["brief"] = True
        return "Daily brief content"

    monkeypatch.setattr("mcp_servers.voice_server._get_daily_brief", mock_brief)
    monkeypatch.setattr("mcp_servers.voice_server.speak_as_employee", lambda *a, **kw: None)
    result = route_intent("what's my brief for today")
    assert called.get("brief") is True


def test_route_intent_hooks(monkeypatch):
    from mcp_servers.voice_server import route_intent
    called = {}

    def mock_hooks(topic, count=10):
        called["hooks"] = True
        return ["hook1", "hook2"]

    monkeypatch.setattr("mcp_servers.voice_server._generate_hooks", mock_hooks)
    monkeypatch.setattr("mcp_servers.voice_server.speak_as_employee", lambda *a, **kw: None)
    result = route_intent("generate some hooks about mixing")
    assert called.get("hooks") is True


def test_get_employee_voice():
    from mcp_servers.voice_server import get_employee_voice
    voice = get_employee_voice("Dwight")
    assert isinstance(voice, str)
    assert len(voice) > 0
