"""
Matches a user's message against your own custom trigger/response pairs.
Still fully rule-based (no AI, no external calls) but smarter than plain
substring matching:

1. Word-boundary matching -- "hi" no longer matches inside "this" or
   "history".
2. Keywords are normalized the same way messages are (punctuation
   stripped) before matching, so "what's up" and "whats up" behave
   identically instead of the apostrophe silently breaking the match.
3. Typo tolerance -- if nothing matches exactly, falls back to fuzzy
   matching so "helo" still triggers a keyword "hello". For multi-word
   phrases, ALL significant words must match (exact or fuzzy) -- a
   single word fuzzy-matching inside an unrelated phrase used to hijack
   the whole reply (e.g. "shubh" alone triggering "contact shubh"'s
   reply even in an unrelated sentence); this is now rejected.
4. Common filler words ("i", "what", "is", "you"...) are excluded from
   fuzzy matching entirely -- they trivially "match" almost any message
   and were causing false positives on totally unrelated text.
5. When multiple triggers match, the most specific (longest) one wins.
"""
import re
import difflib
from typing import Optional

_STOPWORDS = {
    "i", "a", "an", "the", "is", "are", "was", "were", "am", "you", "your",
    "what", "who", "how", "why", "do", "does", "did", "can", "will", "would",
    "should", "this", "that", "it", "of", "in", "on", "at", "to", "for",
    "and", "or", "but", "me", "my", "we", "us", "he", "she", "they",
}
_MIN_FUZZY_WORD_LEN = 4
_MAX_WORDS_FOR_SINGLE_WORD_MATCH = 6  # "please" etc shouldn't hijack a whole real question


def _normalize(text: str) -> str:
    text = text.lower()
    text = re.sub(r"[^\w\s]", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def _significant_words(words: list) -> list:
    """Words worth requiring a match on -- excludes stopwords/too-short."""
    return [w for w in words if w not in _STOPWORDS and len(w) >= _MIN_FUZZY_WORD_LEN]


def find_custom_reply(message: str, custom_replies: list) -> Optional[str]:
    norm_msg = _normalize(message)
    if not norm_msg:
        return None
    msg_words = norm_msg.split()

    best_match = None
    best_score = -1.0

    # Pass 1: exact word-boundary matches (keyword normalized the same
    # way as the message, so punctuation differences don't break this)
    for entry in custom_replies:
        raw_keywords = [k.strip() for k in entry.trigger.split(",") if k.strip()]
        for raw_kw in raw_keywords:
            kw = _normalize(raw_kw)
            if not kw:
                continue
            kw_words = kw.split()
            # A single generic word (e.g. "please") shouldn't hijack a
            # long, substantive message just because the word appears
            # somewhere in it -- only counts if the message itself is short.
            if len(kw_words) == 1 and len(msg_words) > _MAX_WORDS_FOR_SINGLE_WORD_MATCH:
                continue
            pattern = r"\b" + r"\s+".join(re.escape(w) for w in kw_words) + r"\b"
            if re.search(pattern, norm_msg):
                score = len(kw)
                if score > best_score:
                    best_score = score
                    best_match = entry.response

    if best_match is not None:
        return best_match

    # Pass 2: no exact match -- fuzzy typo tolerance. For a single-word
    # keyword, a fuzzy match on that word is enough. For a multi-word
    # phrase, ALL of its significant words must match (exact or fuzzy) --
    # partial overlap on one word is not enough to fire the whole reply.
    for entry in custom_replies:
        raw_keywords = [k.strip() for k in entry.trigger.split(",") if k.strip()]
        for raw_kw in raw_keywords:
            kw = _normalize(raw_kw)
            if not kw:
                continue
            kw_words = kw.split()
            sig_words = _significant_words(kw_words)
            if not sig_words:
                continue  # keyword is entirely stopwords/too short -- skip

            # A multi-word phrase that reduces to just ONE significant
            # word (the rest being stopwords/too-short) shouldn't fuzzy-
            # match on that lone word alone -- e.g. "what is gms chatbot"
            # reducing to just "chatbot" would then match ANY message
            # that happens to mention "chatbot", regardless of context.
            if len(kw_words) > 1 and len(sig_words) < 2:
                continue

            # Same short-message gate as pass 1, for genuinely single-word keywords
            if len(kw_words) == 1 and len(msg_words) > _MAX_WORDS_FOR_SINGLE_WORD_MATCH:
                continue

            # Only match against non-stopword message words -- matching a
            # keyword word against a filler word like "what"/"is" carries
            # no real signal, even via exact/fuzzy comparison.
            msg_candidates = [w for w in msg_words if w not in _STOPWORDS]

            all_matched = True
            for w in sig_words:
                if w in msg_candidates:
                    continue
                if difflib.get_close_matches(w, msg_candidates, n=1, cutoff=0.82):
                    continue
                all_matched = False
                break

            if all_matched:
                score = len(kw) * 0.5  # fuzzy matches rank below exact ones
                if score > best_score:
                    best_score = score
                    best_match = entry.response

    return best_match
