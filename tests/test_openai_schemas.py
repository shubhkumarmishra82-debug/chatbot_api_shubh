import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.observability import estimate_tokens
from app.openai_schemas import ChatCompletionRequest, OAIMessage


def test_estimate_tokens_empty():
    assert estimate_tokens("") == 0


def test_estimate_tokens_roughly_chars_over_4():
    assert estimate_tokens("a" * 40) == 10


def test_estimate_tokens_minimum_one():
    assert estimate_tokens("hi") == 1


def test_chat_request_parses_minimal_payload():
    req = ChatCompletionRequest(messages=[OAIMessage(role="user", content="hi")])
    assert req.model == "gms-default"
    assert req.stream is False
    assert req.use_documents is True
    assert req.web_search is None


def test_chat_request_accepts_extension_fields():
    req = ChatCompletionRequest(
        messages=[OAIMessage(role="user", content="hi")],
        web_search=True,
        use_documents=False,
    )
    assert req.web_search is True
    assert req.use_documents is False
