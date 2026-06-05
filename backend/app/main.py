from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import auth, search
from app.core.config import get_settings

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: nothing needed — Alembic handles migrations separately
    yield
    # Shutdown: SQLAlchemy disposes the engine pool automatically


app = FastAPI(
    title="PrecoBOT API",
    description="Scraping + price analysis for Brazilian marketplaces",
    version="0.1.0",
    docs_url="/docs" if settings.ENVIRONMENT == "development" else None,
    redoc_url=None,
    lifespan=lifespan,
)

# ── CORS ──────────────────────────────────────────────────────────────────
# The frontend origin must be in ALLOWED_ORIGINS (.env)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routes ────────────────────────────────────────────────────────────────
app.include_router(auth.router, prefix="/api/v1")
app.include_router(search.router, prefix="/api/v1")


@app.get("/health", tags=["meta"])
async def health():
    return {"status": "ok", "environment": settings.ENVIRONMENT}
