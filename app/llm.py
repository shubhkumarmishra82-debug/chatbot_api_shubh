"""
Client for YOUR OWN self-hosted model server -- no third-party AI vendor,
no API key from any company. This talks to Ollama (https://ollama.com)
running on a machine you control (a VPS, your PC, etc.), using Ollama's
own HTTP API format.

This is genuinely optional: if OWN_SERVER_URL isn't set, the rest of the
app keeps working fine using just custom replies + document search +
Google search. Setting this is what upgrades it to real conversational AI.

--------------------------------------------------------------------------
Setup (on a server YOU control -- Vercel can't run this itself, it needs
a real always-on machine):

  1. Get a small VPS. Oracle Cloud's "Always Free" tier includes a real
     VM for free, permanently (not a trial) -- a solid no-cost option.
     Any VPS works (Hetzner, DigitalOcean, your own PC with port
     forwarding, etc.)
  2. On that server: install Ollama, pull a model:
       curl -fsSL https://ollama.com/install.sh | sh
       ollama pull llama3.1
  3. By default Ollama only listens on localhost. To let your Vercel
     function reach it, expose it (bind to 0.0.0.0 or use a tunnel like
     Cloudflare Tunnel / ngrok), and put a reverse proxy with basic auth
     or an IP allowlist in front of it -- Ollama itself has no built-in
     auth, so don't expose it to the raw internet unprotected.
  4. Set OWN_SERVER_URL to that server's address, e.g.
     https://your-server.example.com or http://1.2.3.4:11434
--------------------------------------------------------------------------
"""
import os
import httpx

OWN_SERVER_URL = os.getenv("OWN_SERVER_URL")  # e.g. https://your-server.example.com
OWN_SERVER_MODEL = os.getenv("OWN_SERVER_MODEL", "llama3.1")
# Optional: if you put your own auth (e.g. a reverse proxy) in front of
# Ollama, set this and it's sent as a Bearer token -- purely your own
# secret, not issued by any AI company.
OWN_SERVER_TOKEN = os.getenv("OWN_SERVER_TOKEN")


async def generate_reply(messages: list[dict]) -> str:
    """
    messages: list of {"role": "system"|"user"|"assistant", "content": "..."}
    """
    if not OWN_SERVER_URL:
        raise RuntimeError("OWN_SERVER_URL is not set.")

    headers = {}
    if OWN_SERVER_TOKEN:
        headers["Authorization"] = f"Bearer {OWN_SERVER_TOKEN}"

    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.post(
            f"{OWN_SERVER_URL.rstrip('/')}/api/chat",
            headers=headers,
            json={
                "model": OWN_SERVER_MODEL,
                "messages": messages,
                "stream": False,
            },
        )
        response.raise_for_status()
        data = response.json()
        return data["message"]["content"]
