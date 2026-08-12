"""
The modular AI router. Tries configured providers in order, with retries
and a timeout per attempt. To add a new provider later: write a class
implementing AIProvider, add one line to PROVIDERS below. Nothing else
in the app needs to change.

Currently only OwnServerProvider is registered -- by design, no AI
vendor key ships in this codebase. If you ever want to add one (e.g. a
Groq-backed provider), it's a single new file plus one line here.
"""
import asyncio
import logging
from typing import Dict, List

from .own_server import OwnServerProvider

log = logging.getLogger("gms.ai_router")

PROVIDERS = [
    OwnServerProvider(),
]

DEFAULT_RETRIES = 1
RETRY_DELAY_SECONDS = 0.6
PER_ATTEMPT_TIMEOUT = 45.0


class AllProvidersFailedError(Exception):
    pass


class AIRouter:
    def __init__(self, providers=None):
        self.providers = providers if providers is not None else PROVIDERS

    def is_configured(self) -> bool:
        return any(p.is_configured() for p in self.providers)

    def active_provider_name(self) -> str:
        for p in self.providers:
            if p.is_configured():
                return p.name
        return "none"

    async def chat(self, messages: List[Dict], request_id: str = "-", **kwargs) -> str:
        last_error = None
        for provider in self.providers:
            if not provider.is_configured():
                continue
            for attempt in range(DEFAULT_RETRIES + 1):
                try:
                    return await asyncio.wait_for(
                        provider.chat(messages, **kwargs), timeout=PER_ATTEMPT_TIMEOUT
                    )
                except Exception as e:
                    last_error = e
                    log.warning(
                        "[%s] provider=%s attempt=%d failed: %s",
                        request_id, provider.name, attempt, e,
                    )
                    if attempt < DEFAULT_RETRIES:
                        await asyncio.sleep(RETRY_DELAY_SECONDS)
        raise AllProvidersFailedError(str(last_error) if last_error else "No provider configured")

    async def chat_stream(self, messages: List[Dict], request_id: str = "-", **kwargs):
        for provider in self.providers:
            if provider.is_configured():
                async for chunk in provider.chat_stream(messages, **kwargs):
                    yield chunk
                return
        raise AllProvidersFailedError("No provider configured")


router = AIRouter()
