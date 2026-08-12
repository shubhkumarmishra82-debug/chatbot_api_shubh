"""
Backwards-compatible wrapper around the new modular provider router
(app/providers/) -- kept so /chat (the simpler widget endpoint) doesn't
need rewriting. /v1/chat/completions uses app/providers directly.
"""
from .providers import router as _router
from .providers.own_server import OwnServerProvider

_own = OwnServerProvider()
OWN_SERVER_URL = _own.url
OWN_SERVER_MODEL = _own.model
OWN_SERVER_TOKEN = _own.token


def is_configured() -> bool:
    return _router.is_configured()


def active_provider() -> str:
    return _router.active_provider_name()


async def generate_reply(messages: list) -> str:
    return await _router.chat(messages)
