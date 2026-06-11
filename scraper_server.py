"""
Scraper Server — runs independently on port 8001.

Start with:
    python scraper_server.py

This process owns its own event loop with no interference from FastAPI.
Playwright and SeleniumBase work normally here.
"""
import asyncio
import sys
from pathlib import Path

# ── Windows event loop fix (must be before any asyncio usage) ─────────────
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
import uvicorn

# ── Add the src/ folder to path so scraper.py is importable ──────────────
SRC_PATH = Path(__file__).parent / "src"
sys.path.insert(0, str(SRC_PATH))

try:
    from scraper import run_scraper as _run_scraper
except ImportError as e:
    print(f"\n❌ Could not import scraper.py from {SRC_PATH}")
    print(f"   Error: {e}")
    print("   Make sure src/scraper.py exists.\n")
    sys.exit(1)

# ── App ───────────────────────────────────────────────────────────────────
app = FastAPI(
    title="Scraper Server",
    description="Internal scraping service. Not exposed to the internet.",
    version="0.1.0",
)


class ScrapeRequest(BaseModel):
    query: str = Field(min_length=2, max_length=500)
    marketplaces: list[str] = Field(default_factory=lambda: ["mercadolivre"])
    max_results: int = Field(default=20, ge=1, le=100)


class ScrapeResponse(BaseModel):
    results: list[dict]
    count: int


@app.post("/scrape", response_model=ScrapeResponse)
async def scrape(body: ScrapeRequest):
    """
    Run the scraper and return raw results.
    Called internally by the FastAPI backend — never by the frontend directly.
    """
    try:
        results = await _run_scraper(
            query=body.query,
            marketplaces=body.marketplaces,
            max_results=body.max_results,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Scraper error: {str(e)}")

    return ScrapeResponse(results=results, count=len(results))


@app.get("/health")
def health():
    return {"status": "ok", "service": "scraper"}


# ── Entry point ───────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("🔍 Scraper server starting on http://localhost:8001")
    print("   Health check: http://localhost:8001/health")
    print("   Press Ctrl+C to stop\n")
    uvicorn.run(
        app,
        host="127.0.0.1",
        port=8001,
        loop="asyncio",      # explicitly use asyncio loop (not uvicorn default)
    )
