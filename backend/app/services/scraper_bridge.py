"""
Scraper bridge — talks to the scraper server over HTTP.

The scraper server runs as a separate process on port 8001.
This means Playwright runs in its own event loop, completely
isolated from FastAPI. No more Windows event loop conflicts.

Start the scraper server before starting the backend:
    python scraper_server.py
"""
import httpx

from app.services.analytics import parse_price_brl

SCRAPER_SERVER_URL = "http://127.0.0.1:8001"
# Timeout in seconds — scraping can be slow, so we give it 2 minutes
SCRAPER_TIMEOUT = 120.0


async def run_scraper(
    query: str,
    marketplaces: list[str],
    max_results: int,
) -> list[dict]:
    """
    Ask the scraper server to run a search and return results.
    Raises a clear error if the scraper server is not running.
    """
    payload = {
        "query": query,
        "marketplaces": marketplaces,
        "max_results": max_results,
    }

    async with httpx.AsyncClient(timeout=SCRAPER_TIMEOUT) as client:
        try:
            response = await client.post(
                f"{SCRAPER_SERVER_URL}/scrape",
                json=payload,
            )
            response.raise_for_status()

        except httpx.ConnectError:
            raise RuntimeError(
                "Scraper server is not running. "
                "Start it with: python scraper_server.py"
            )
        except httpx.HTTPStatusError as e:
            raise RuntimeError(
                f"Scraper server returned an error: {e.response.text}"
            )

    raw_results: list[dict] = response.json()["results"]

    # Normalise keys to match what the rest of the backend expects
    for item in raw_results:
        # Parse the price string into a float
        item["price_brl"] = parse_price_brl(item.get("price"))
        # Rename "price" → "price_raw"
        item["price_raw"] = item.pop("price", None)
        # Rename "image" → "image_url" if your scraper uses that key
        if "image" in item and "image_url" not in item:
            item["image_url"] = item.pop("image")
        item.setdefault("image_url", None)
        item.setdefault("marketplace", marketplaces[0])

    return raw_results
