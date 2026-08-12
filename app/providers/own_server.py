"""
Your own self-hosted Ollama-compatible server. No vendor, no API key
from any AI company -- talks to a machine you control.
"""
import json
import os
import httpx

from .base import AIProvider


class OwnServerProvider(AIProvider):
    name = "own_server"

    def __init__(self):
        self.url = os.getenv("OWN_SERVER_URL")
        self.model = os.getenv("OWN_SERVER_MODEL", "llama3.1")
        self.token = os.getenv("OWN_SERVER_TOKEN")

    def is_configured(self) -> bool:
        return bool(self.url)

    def _headers(self) -> dict:
        headers = {}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        return headers

    async def chat(self, messages, **kwargs) -> str:
        if not self.is_configured():
            raise RuntimeError("OWN_SERVER_URL is not set.")
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{self.url.rstrip('/')}/api/chat",
                headers=self._headers(),
                json={"model": self.model, "messages": messages, "stream": False},
            )
            response.raise_for_status()
            data = response.json()
            return data["message"]["content"]

    async def chat_stream(self, messages, **kwargs):
        if not self.is_configured():
            raise RuntimeError("OWN_SERVER_URL is not set.")
        async with httpx.AsyncClient(timeout=120.0) as client:
            async with client.stream(
                "POST",
                f"{self.url.rstrip('/')}/api/chat",
                headers=self._headers(),
                json={"model": self.model, "messages": messages, "stream": True},
            ) as response:
                response.raise_for_status()
                async for line in response.aiter_lines():
                    if not line:
                        continue
                    try:
                        chunk = json.loads(line)
                    except json.JSONDecodeError:
                        continue
                    content = chunk.get("message", {}).get("content", "")
                    if content:
                        yield content
                    if chunk.get("done"):
                        break
