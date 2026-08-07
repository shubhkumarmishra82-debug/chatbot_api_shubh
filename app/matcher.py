"""
Matches a user's message against your own custom trigger/response pairs.
Still fully rule-based (no AI, no external calls) but smarter than plain
substring matching:

1. Word-boundary matching -- "hi" no longer matches inside "this" or
   "history".
2. Multi-word phrases still match as phrases (e.g. "who made you").
3. Typo tolerance -- if nothing matches exactly, falls back to fuzzy
   matching so "helo" still triggers a keyword "hello".
4. When multiple triggers match, the most specific (longest) one wins.
"""
import re
import difflib
from typing import Optional


def _normalize(text: str) -> str:
    # lowercase, strip punctuation down to spaces, collapse whitespace
    text = text.lower()
    text = re.sub(r"[^\w\s]", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def find_custom_reply(message: str, custom_replies: list) -> Optional[str]:
    norm_msg = _normalize(message)
    if not norm_msg:
        return None

    best_match = None
    best_score = -1.0

    # Pass 1: exact word-boundary matches (handles single words and phrases)
    for entry in custom_replies:
        keywords = [k.strip().lower() for k in entry.trigger.split(",") if k.strip()]
        for kw in keywords:
            pattern = r"\b" + r"\s+".join(re.escape(w) for w in kw.split()) + r"\b"
            if re.search(pattern, norm_msg):
                score = len(kw)  # longer/more specific keyword wins
                if score > best_score:
                    best_score = score
                    best_match = entry.response

    if best_match is not None:
        return best_match

    # Pass 2: no exact match -- try fuzzy matching for typos, word by word
    msg_words = norm_msg.split()
    for entry in custom_replies:
        keywords = [k.strip().lower() for k in entry.trigger.split(",") if k.strip()]
        for kw in keywords:
            for kw_word in kw.split():
                close = difflib.get_close_matches(kw_word, msg_words, n=1, cutoff=0.82)
                if close:
                    score = len(kw) * 0.5  # fuzzy matches rank below exact ones
                    if score > best_score:
                        best_score = score
                        best_match = entry.response

    return best_match
