"""
Matches a user's message against your own custom trigger/response pairs.
Simple, transparent keyword matching -- no AI involved. Longer/more
specific triggers win if multiple match.
"""
from typing import Optional


def find_custom_reply(message: str, custom_replies: list) -> Optional[str]:
    lower_msg = message.lower()
    best_match = None
    best_len = -1

    for entry in custom_replies:
        keywords = [k.strip().lower() for k in entry.trigger.split(",") if k.strip()]
        for kw in keywords:
            if kw and kw in lower_msg and len(kw) > best_len:
                best_match = entry.response
                best_len = len(kw)

    return best_match
