"""
Wraps Google's official Custom Search JSON API (free tier: 100 queries/day).

Design: results are returned to the user AS search results -- title,
snippet, and link, clearly labeled as "here's what I found." Nothing is
reworded or repackaged to look like original writing. This is the safe,
transparent way to surface Google's content: point to it, don't disguise it.

Setup:
1. Enable "Custom Search API" at https://console.cloud.google.com
2. Create a Programmable Search Engine at https://programmablesearchengine.google.com
   (set it to search the entire web)
3. Set env vars: GOOGLE_API_KEY, GOOGLE_CSE_ID
"""
import os
import re
import httpx

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
GOOGLE_CSE_ID = os.getenv("GOOGLE_CSE_ID")
GOOGLE_SEARCH_URL = "https://www.googleapis.com/customsearch/v1"

QUESTION_WORDS = [
    "what", "who", "why", "how", "when", "where", "which", "whom", "whose",
    "is ", "are ", "can ", "does ", "do ", "define", "explain", "meaning of",
]

PROBLEM_KEYWORDS = [
    "solve", "calculate", "derivative", "integral", "equation", "velocity",
    "acceleration", "force", "prove", "simplify", "factorize", "factorise",
    "theorem", "formula", "physics", "chemistry", "mathematics", "problem",
    "compute", "find x",
]


def looks_like_question(message: str) -> bool:
    """Broad heuristic: does this look like something Google should answer?"""
    stripped = message.strip().lower()
    if stripped.endswith("?"):
        return True
    if any(stripped.startswith(w) for w in QUESTION_WORDS):
        return True
    if any(kw in stripped for kw in PROBLEM_KEYWORDS):
        return True
    if re.search(r"\d+\s*[\+\-\*/=]\s*[\dx]", stripped):
        return True
    return False


async def google_search(query: str, num: int = 3) -> list[dict]:
    if not (GOOGLE_API_KEY and GOOGLE_CSE_ID):
        return []

    async with httpx.AsyncClient(timeout=15.0) as client:
        try:
            response = await client.get(
                GOOGLE_SEARCH_URL,
                params={
                    "key": GOOGLE_API_KEY,
                    "cx": GOOGLE_CSE_ID,
                    "q": query,
                    "num": num,
                },
            )
            response.raise_for_status()
        except httpx.HTTPError:
            return []

        data = response.json()
        return [
            {
                "title": item.get("title", ""),
                "snippet": item.get("snippet", ""),
                "link": item.get("link", ""),
            }
            for item in data.get("items", [])[:num]
        ]


def format_search_reply(results: list[dict]) -> str:
    """Builds a plain-text reply that clearly presents these as search
    results, not as the bot's own original writing."""
    if not results:
        return "I searched but couldn't find anything useful. Try rephrasing?"
    lines = ["Here's what I found:"]
    for r in results:
        lines.append(f"\n**{r['title']}**\n{r['snippet']}\n{r['link']}")
    return "\n".join(lines)
