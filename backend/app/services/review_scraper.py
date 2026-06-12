"""
Review scraper for Mercado Livre.

Navigates to a product page, clicks through the star rating
dropdown, and collects N reviews per star level.

Sends requests to the scraper server (port 8001) to avoid
running Playwright inside FastAPI's event loop.
"""
import httpx
from app.schemas.schemas import ReviewsByStars
from app.core.constants import REVIEWS_PER_STAR

SCRAPER_SERVER_URL = "http://127.0.0.1:8001"
SCRAPER_TIMEOUT = 120.0


async def scrape_reviews(
    product_url: str,
    marketplace: str,
    reviews_per_star: int = REVIEWS_PER_STAR,
) -> ReviewsByStars:
    """
    Ask the scraper server to collect reviews by star rating.
    Returns a ReviewsByStars object.
    """
    payload = {
        "product_url": product_url,
        "marketplace": marketplace,
        "reviews_per_star": reviews_per_star,
    }

    async with httpx.AsyncClient(timeout=SCRAPER_TIMEOUT) as client:
        try:
            response = await client.post(
                f"{SCRAPER_SERVER_URL}/scrape-reviews",
                json=payload,
            )
            response.raise_for_status()
        except httpx.ConnectError:
            print("[reviews] Scraper server não está rodando.")
            return ReviewsByStars()
        except Exception as e:
            print(f"[reviews] Erro: {e}")
            return ReviewsByStars()

    data = response.json()
    return ReviewsByStars(**data)
