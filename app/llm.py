"""
AI provider layer -- ONLY supports your own self-hosted server. No
third-party AI vendor, no API key from any company, by design.

If OWN_SERVER_URL is set, it's used (e.g. Ollama running on your own
Oracle Cloud instance, home PC, or any VPS you control). If it's not
set, AI is simply off -- the app still works fine using your custom
replies, your documents, and search results.
"""
import os
import httpx

OWN_SERVER_URL = os.getenv("OWN_SERVER_URL")
OWN_SERVER_MODEL = os.getenv("OWN_SERVER_MODEL", "llama3.1")
OWN_SERVER_TOKEN = os.getenv("OWN_SERVER_TOKEN")


def is_configured() -> bool:
    return bool(OWN_SERVER_URL)


def active_provider() -> str:
    return "own_server" if OWN_SERVER_URL else "none"


async def generate_reply(messages: list[dict]) -> str:
    """
    messages: list of {"role": "system"|"user"|"assistant", "content": "..."}
    """
    if not OWN_SERVER_URL:
        raise RuntimeError("No AI server configured (set OWN_SERVER_URL to your own server).")

    headers = {}
    if OWN_SERVER_TOKEN:
        headers["Authorization"] = f"Bearer {OWN_SERVER_TOKEN}"

    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.post(
            f"{OWN_SERVER_URL.rstrip('/')}/api/chat",
            headers=headers,
            json={"model": OWN_SERVER_MODEL, "messages": messages, "stream": False},
        )
        response.raise_for_status()
        data = response.json()
        return data["message"]["content"]
