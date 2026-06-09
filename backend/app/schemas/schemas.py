"""
Pydantic v2 schemas.

Naming convention:
  <Entity>Create  → request body for POST
  <Entity>Out     → response body (never exposes hashed_password)
"""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field, field_validator


# ── Auth ──────────────────────────────────────────────────────────────────


class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    full_name: Optional[str] = Field(default=None, max_length=120)


class UserOut(BaseModel):
    id: int
    email: EmailStr
    full_name: Optional[str]
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenPair(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshRequest(BaseModel):
    refresh_token: str


# ── Search ────────────────────────────────────────────────────────────────


SUPPORTED_MARKETPLACES = [
    "mercadolivre",
    "olx",
    "shopee",
    "americanas",
    "magazineluiza",
]


class SearchRequest(BaseModel):
    query: str = Field(min_length=2, max_length=500)
    marketplaces: list[str] = Field(default_factory=lambda: ["mercadolivre"])
    max_results: int = Field(default=20, ge=1, le=100)

    @field_validator("marketplaces")
    @classmethod
    def validate_marketplaces(cls, v: list[str]) -> list[str]:
        invalid = set(v) - set(SUPPORTED_MARKETPLACES)
        if invalid:
            raise ValueError(f"Marketplaces não suportados: {invalid}")
        return v


class ResultOut(BaseModel):
    id: int
    marketplace: str
    title: str
    link: str
    price_raw: Optional[str]
    price_brl: Optional[float]
    rating: Optional[str]
    condition: str
    shipping: str
    image_url: Optional[str]

    model_config = {"from_attributes": True}


class SearchOut(BaseModel):
    id: int
    query: str
    marketplaces: str
    max_results: int
    result_count: int
    created_at: datetime
    results: list[ResultOut] = []

    model_config = {"from_attributes": True}


# ── Price analytics ───────────────────────────────────────────────────────


class PriceAnalysis(BaseModel):
    """Computed price intelligence returned alongside search results."""
    count: int
    min_price: Optional[float]
    max_price: Optional[float]
    mean_price: Optional[float]
    median_price: Optional[float]
    # IQR-filtered mean — more reliable than plain mean
    iqr_mean: Optional[float]
    # Price you'd need to beat 20% of cheapest listings
    competitive_floor: Optional[float]
    # Suggested sell price at a given markup over the IQR mean
    suggested_price_10pct: Optional[float]
    suggested_price_20pct: Optional[float]
    suggested_price_30pct: Optional[float]
    currency: str = "BRL"


class SearchResponse(BaseModel):
    """Full response returned after a scrape."""
    search: SearchOut
    analysis: PriceAnalysis
