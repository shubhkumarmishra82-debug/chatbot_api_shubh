"""
A simple in-memory cache for identical chat requests. IMPORTANT honest
limitation: on serverless (Vercel), each cold start gets fresh memory,
so this only helps for repeat requests hitting the same warm instance
within a short window -- it is NOT a distributed cache. For guaranteed
cross-instance caching you'd need an external store (e.g. Redis via
Upstash), which is a reasonable next step if this matters at your scale.
"""
import hashlib
import json
import time

_cache: dict = {}
DEFAULT_TTL_SECONDS = 120


def _key_for(messages: list, model: str) -> str:
    raw = json.dumps({"m": messages, "model": model}, sort_keys=True)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def get(messages: list, model: str):
    key = _key_for(messages, model)
    entry = _cache.get(key)
    if not entry:
        return None
    value, expires_at = entry
    if time.time() > expires_at:
        _cache.pop(key, None)
        return None
    return value


def set(messages: list, model: str, value, ttl: int = DEFAULT_TTL_SECONDS):
    key = _key_for(messages, model)
    _cache[key] = (value, time.time() + ttl)
