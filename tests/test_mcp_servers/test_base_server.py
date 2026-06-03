from unittest.mock import patch, MagicMock


def test_call_ollama_returns_text():
    from mcp_servers.base_server import call_ollama
    mock_resp = MagicMock()
    mock_resp.message.content = "This is the response"
    with patch("ollama.chat", return_value=mock_resp):
        result = call_ollama("llama3.1:8b", "Say hello")
    assert result == "This is the response"


def test_call_ollama_with_system_prompt():
    from mcp_servers.base_server import call_ollama
    mock_resp = MagicMock()
    mock_resp.message.content = "response"
    with patch("ollama.chat", return_value=mock_resp) as mock_chat:
        call_ollama("llama3.1:8b", "user msg", system="be concise")
    messages = mock_chat.call_args[1]["messages"]
    assert messages[0]["role"] == "system"
    assert messages[1]["role"] == "user"
