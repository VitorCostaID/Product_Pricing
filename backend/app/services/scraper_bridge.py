"""
Bridge between FastAPI and the existing scraper.

The scraper lives in /app/scraper_src/scraper.py (mounted by Docker).
We import it at runtime so you can keep editing scraper.py without
touching this file.

product_details shape expected from scraper.py:
  {
    "title":     str,
    "link":      str,
    "rating":    str,
    "price":     str,   ← the aria-label string, e.g. "R$ 1.299,90"
    "condition": str,
    "shipping":  str,
    "image_url": str,   ← optional, add to your scraper when ready
  }
"""
import asyncio
import importlib.util
import sys
from pathlib import Path
from typing import Any

from app.services.analytics import parse_price_brl


def _load_scraper():
    """Dynamically import scraper.py from the mounted volume."""
    scraper_path = Path("/app/scraper_src/scraper.py")

    if not scraper_path.exists():
        raise FileNotFoundError(
            f"scraper.py not found at {scraper_path}. "
            "Check that the ./src volume is mounted correctly in docker-compose.yml."
        )

    spec = importlib.util.spec_from_file_location("scraper", scraper_path)
    module = importlib.util.module_from_spec(spec)
    sys.modules["scraper"] = module
    spec.loader.exec_module(module)
    return module


def _run_scraper_sync(
    query: str,
    marketplaces: list[str],
    max_results: int,
) -> list[dict[str, Any]]:
    """Call run_scraper() synchronously (blocking)."""
    scraper = _load_scraper()
    return scraper.run_scraper(
        query=query,
        marketplaces=marketplaces,
        max_results=max_results,
    )


async def run_scraper(
    query: str,
    marketplaces: list[str],
    max_results: int,
) -> list[dict[str, Any]]:
    """
    Async wrapper: runs the blocking scraper in a thread pool so
    FastAPI's event loop is never blocked.

    Returns a list of product_details dicts enriched with price_brl.
    """
    loop = asyncio.get_running_loop()
    raw_results: list[dict] = await loop.run_in_executor(
        None,  # default ThreadPoolExecutor
        _run_scraper_sync,
        query,
        marketplaces,
        max_results,
    )

    # Enrich each result with the parsed float price
    for item in raw_results:
        item["price_brl"] = parse_price_brl(item.get("price"))
        # Normalise key: scraper uses "price" (aria-label), we store as price_raw
        item.setdefault("price_raw", item.pop("price", None))
        item.setdefault("image_url", None)

    return raw_results