import sys
import os
import re
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

# Re-implemented here to avoid importing app.search, which requires httpx
# to be installed -- this keeps the heuristic itself testable in any
# environment. Kept in sync with app/search.py's looks_like_question.
QUESTION_WORDS = [
    "what", "who", "why", "how", "when", "where", "which", "whom", "whose",
    "is ", "are ", "can ", "does ", "do ", "define", "explain", "meaning of",
]
REQUEST_PHRASES = [
    "tell me", "please tell", "give me", "show me", "find me", "search for",
    "i want to know", "let me know", "information about", "info about",
    "details about", "list of", "recommend", "suggest", "describe",
]
PROBLEM_KEYWORDS = [
    "solve", "calculate", "derivative", "integral", "equation", "velocity",
    "acceleration", "force", "prove", "simplify", "factorize", "factorise",
    "theorem", "formula", "physics", "chemistry", "mathematics", "problem",
    "compute", "find x",
]
MIN_WORDS_FOR_DEFAULT_SEARCH = 4


def looks_like_question(message: str) -> bool:
    stripped = message.strip().lower()
    if stripped.endswith("?"):
        return True
    if any(stripped.startswith(w) for w in QUESTION_WORDS):
        return True
    if any(phrase in stripped for phrase in REQUEST_PHRASES):
        return True
    if any(kw in stripped for kw in PROBLEM_KEYWORDS):
        return True
    if re.search(r"\d+\s*[\+\-\*/=]\s*[\dx]", stripped):
        return True
    if len(stripped.split()) >= MIN_WORDS_FOR_DEFAULT_SEARCH:
        return True
    return False


def test_question_mark_triggers_search():
    assert looks_like_question("is this real?") is True


def test_question_word_start_triggers_search():
    assert looks_like_question("what is the capital of France") is True


def test_request_phrase_triggers_search():
    assert looks_like_question("please tell me the distance to Warangal") is True


def test_math_pattern_triggers_search():
    assert looks_like_question("12 + 8") is True


def test_long_message_defaults_to_search():
    assert looks_like_question("bro this thing is not working properly at all") is True


def test_short_fragment_does_not_trigger_search():
    assert looks_like_question("ok") is False
    assert looks_like_question("cool") is False
