"""
Rough token estimation (no tiktoken dependency, keeps the deploy light)
and structured logging setup. The token count is an approximation
(chars/4, a commonly-used rule of thumb for English text) -- good enough
for usage tracking and rate-limit-adjacent decisions, not exact.
"""
import logging
import sys


def estimate_tokens(text: str) -> int:
    if not text:
        return 0
    return max(1, len(text) // 4)


def setup_logging():
    logger = logging.getLogger("gms")
    if logger.handlers:
        return logger  # already configured (e.g. re-imported on warm invocation)
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(
        logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s")
    )
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)
    return logger
