import os
import tomllib
from pathlib import Path

_DEFAULT = Path(__file__).parent / "settings.toml"

def load_settings() -> dict:
    path = Path(os.environ.get("SOCIALDEPT_CONFIG", str(_DEFAULT)))
    with open(path, "rb") as f:
        return tomllib.load(f)
