"""
Simple retrieval over YOUR OWN documents -- no AI, no embeddings, no
external service. Splits each document into overlapping chunks, scores
each chunk against the question by word overlap, returns the best ones.
This is what lets the bot answer from your own material instead of the
open web.
"""
import re
from typing import List


def _tokenize(text: str) -> List[str]:
    return [_stem(w) for w in re.findall(r"[a-z0-9']+", text.lower())]


def _stem(word: str) -> str:
    """Very lightweight suffix stripping so 'refund'/'refunds',
    'running'/'run' etc overlap without needing a real NLP dependency."""
    for suffix in ("ing", "ed", "es", "s"):
        if len(word) > len(suffix) + 2 and word.endswith(suffix):
            return word[: -len(suffix)]
    return word


def chunk_text(text: str, chunk_size: int = 220, overlap: int = 40) -> List[str]:
    words = text.split()
    if not words:
        return []
    chunks = []
    start = 0
    while start < len(words):
        end = start + chunk_size
        chunks.append(" ".join(words[start:end]))
        start += chunk_size - overlap
    return chunks


def top_chunks_for_query(query: str, documents: list, top_n: int = 3) -> List[dict]:
    """
    documents: list of DB Document rows (id, title, content)
    Returns up to top_n {"title": ..., "text": ...} chunks, best overlap first.
    """
    query_words = set(_tokenize(query))
    if not query_words:
        return []

    scored = []
    for doc in documents:
        for chunk in chunk_text(doc.content):
            chunk_words = _tokenize(chunk)
            if not chunk_words:
                continue
            overlap = len(query_words.intersection(chunk_words))
            if overlap > 0:
                scored.append({"score": overlap, "title": doc.title, "text": chunk})

    scored.sort(key=lambda x: x["score"], reverse=True)
    return scored[:top_n]
