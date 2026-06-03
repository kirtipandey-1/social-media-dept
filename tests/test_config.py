import os
from pathlib import Path
import tomllib

def test_load_settings_returns_telegram_keys(tmp_path, monkeypatch):
    toml = tmp_path / "settings.toml"
    toml.write_text('[telegram]\nbot_token = "mytoken"\nchat_id = "123"\n')
    monkeypatch.setenv("SOCIALDEPT_CONFIG", str(toml))
    from config import load_settings
    s = load_settings()
    assert s["telegram"]["bot_token"] == "mytoken"
    assert s["telegram"]["chat_id"] == "123"

def test_load_settings_uses_env_override(tmp_path, monkeypatch):
    toml = tmp_path / "custom.toml"
    toml.write_text('[telegram]\nbot_token = "override"\nchat_id = "456"\n')
    monkeypatch.setenv("SOCIALDEPT_CONFIG", str(toml))
    from config import load_settings
    s = load_settings()
    assert s["telegram"]["bot_token"] == "override"
