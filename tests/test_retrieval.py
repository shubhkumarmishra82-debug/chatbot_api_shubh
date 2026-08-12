import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.retrieval import chunk_text, top_chunks_for_query


class FakeDoc:
    def __init__(self, title, content):
        self.title = title
        self.content = content


def test_chunk_text_splits_long_text():
    text = " ".join(["word"] * 500)
    chunks = chunk_text(text, chunk_size=220, overlap=40)
    assert len(chunks) > 1


def test_chunk_text_empty_returns_empty_list():
    assert chunk_text("") == []


def test_top_chunks_finds_relevant_document():
    docs = [
        FakeDoc("Refund Policy", "We offer refunds within 30 days of purchase for any reason."),
        FakeDoc("Shipping Info", "Orders ship within 2 business days via standard courier."),
    ]
    results = top_chunks_for_query("what is your refund policy", docs)
    assert len(results) > 0
    assert results[0]["title"] == "Refund Policy"


def test_top_chunks_no_match_returns_empty():
    docs = [FakeDoc("Refund Policy", "We offer refunds within 30 days.")]
    results = top_chunks_for_query("completely unrelated gibberish zzz qqq", docs)
    assert results == []


def test_top_chunks_empty_query_returns_empty():
    docs = [FakeDoc("Doc", "Some content here.")]
    assert top_chunks_for_query("", docs) == []


def test_top_chunks_respects_top_n():
    docs = [
        FakeDoc(f"Doc {i}", "python programming language tutorial guide")
        for i in range(10)
    ]
    results = top_chunks_for_query("python programming", docs, top_n=3)
    assert len(results) <= 3
