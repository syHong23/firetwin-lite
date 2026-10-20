"""Call a local open-weight LLM served by Ollama (http://localhost:11434).

Only the Python standard library is used, so no extra package is needed.
Temperature is 0 so that the same question gives the same answer
(reproducibility matters when we compare conditions later).
"""
import json
import urllib.request

OLLAMA_URL = "http://localhost:11434/api/chat"
DEFAULT_MODEL = "llama3.1:8b"


def chat(messages: list[dict], model: str = DEFAULT_MODEL, json_mode: bool = False) -> str:
    """Send a whole conversation (system, user and assistant turns) and return the reply."""
    payload = {"model": model, "messages": messages, "stream": False,
               "options": {"temperature": 0}}
    if json_mode:
        payload["format"] = "json"
    request = urllib.request.Request(
        OLLAMA_URL, data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(request, timeout=300) as response:
        data = json.loads(response.read().decode("utf-8"))
    return data["message"]["content"]


def ask(question: str, system: str | None = None, model: str = DEFAULT_MODEL,
        json_mode: bool = False) -> str:
    """Send one question to the local LLM and return its answer as text."""
    messages = [{"role": "system", "content": system}] if system else []
    messages.append({"role": "user", "content": question})
    return chat(messages, model=model, json_mode=json_mode)
