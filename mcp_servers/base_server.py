import ollama
import logging
from config import load_settings

log = logging.getLogger("mcp_servers")


def call_ollama(model: str, prompt: str, system: str | None = None) -> str:
    """Call Ollama with optional system prompt. Returns text content."""
    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})
    response = ollama.chat(model=model, messages=messages)
    return response.message.content


def get_ollama_model() -> str:
    return load_settings().get("ollama", {}).get("model", "llama3.1:8b")


def get_vision_model() -> str:
    return load_settings().get("ollama", {}).get("vision_model", "llava")
