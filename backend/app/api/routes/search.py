from fastapi import APIRouter, status

from app.schemas.schemas import SearchRequest, SearchResponse, SearchOut
from app.services.analytics import compute_price_analysis
from app.services.scraper_bridge import run_scraper

router = APIRouter(prefix="/search", tags=["search"])


@router.post("/", response_model=SearchResponse, status_code=status.HTTP_201_CREATED)
async def run_search(body: SearchRequest):
    """
    Public endpoint (no auth yet).
    Runs the scraper and returns results + price analysis.
    DB persistence is disabled until auth is wired in.
    """
    # 1. Scrape
    raw_results = await run_scraper(
        query=body.query,
        marketplaces=body.marketplaces,
        max_results=body.max_results,
    )

    # 2. Build in-memory result objects (not saved to DB yet)
    result_list = []
    for i, item in enumerate(raw_results):
        result_list.append({
            "id": i,                      # temporary id, just for the frontend key
            "marketplace": item.get("marketplace", body.marketplaces[0]),
            "title":       item.get("title", "Unknown"),
            "link":        item.get("link", "#"),
            "price_raw":   item.get("price_raw"),
            "price_brl":   item.get("price_brl"),
            "rating":      item.get("rating"),
            "condition":   item.get("condition", "New"),
            "shipping":    item.get("shipping", "Not specified"),
            "image_url":   item.get("image_url"),
        })

    # 3. Compute price analysis
    analysis = compute_price_analysis([r["price_brl"] for r in result_list])

    # 4. Build response manually (no DB model needed)
    search_out = SearchOut(
        id=0,
        query=body.query,
        marketplaces=",".join(body.marketplaces),
        max_results=body.max_results,
        result_count=len(result_list),
        created_at=__import__('datetime').datetime.now(__import__('datetime').timezone.utc),
        results=result_list,
    )

    return SearchResponse(search=search_out, analysis=analysis)
