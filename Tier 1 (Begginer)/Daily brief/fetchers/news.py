"""
Fetches top news via Tavily search API.
Runs two searches: general world news + tech/startup news.
"""

from datetime import date
from tavily import TavilyClient


def fetch_news(api_key: str) -> list[dict]:
    client = TavilyClient(api_key=api_key)
    today = date.today().strftime("%B %d, %Y")

    results = []

    for query in [
        f"Top Prague news today {today}",
        f"Top global news today {today}",
        f"Claude, Gemini, OpenAI news today {today}",
        f"Stock market news today {today}",
        f"Cryptocurrency news today {today}",
    ]:
        response = client.search(
            query=query,
            max_results=3,
            search_depth="basic",
            include_answer=False,
        )
        for r in response.get("results", []):
            results.append({
                "title": r.get("title", ""),
                "url": r.get("url", ""),
                "snippet": r.get("content", "")[:300],
            })

    # Deduplicate by URL while preserving order
    seen = set()
    unique = []
    for item in results:
        if item["url"] not in seen:
            seen.add(item["url"])
            unique.append(item)

    return unique[:15]
