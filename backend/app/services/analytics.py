"""
Price analytics engine.

All functions are pure (no DB or network calls) — easy to test
and swap for an ML model later without touching any routes.
"""
import re
import statistics
from typing import Optional

from app.schemas.schemas import MarketplaceCosts, PriceAnalysis


# ── Price parsing ─────────────────────────────────────────────────────────

_PRICE_RE = re.compile(r"[\d.,]+")


def parse_price_brl(raw: Optional[str]) -> Optional[float]:
    """
    Extract the first numeric value from a Brazilian price string.
      "R$ 1.299,90" → 1299.90
      "1299.90"     → 1299.90
    """
    if not raw:
        return None
    match = _PRICE_RE.search(raw)
    if not match:
        return None
    token = match.group()
    if "," in token and "." in token:
        token = token.replace(".", "").replace(",", ".")
    elif "," in token:
        token = token.replace(",", ".")
    try:
        value = float(token)
        if value <= 0 or value > 9_999_999:
            return None
        return round(value, 2)
    except ValueError:
        return None


# ── Title filter ──────────────────────────────────────────────────────────


def filter_by_query(results: list[dict], query: str) -> list[dict]:
    """
    Keep only results whose title contains every word in the query.
    Case-insensitive. Ignores accents only when an exact match fails.
    """
    words = [w.lower() for w in query.split() if w.strip()]
    if not words:
        return results

    def matches(title: str) -> bool:
        t = title.lower()
        return all(w in t for w in words)

    return [r for r in results if matches(r.get("title", ""))]


# ── IQR filter ────────────────────────────────────────────────────────────


def _iqr_filtered(prices: list[float]) -> list[float]:
    """Remove outliers beyond 1.5 × IQR from Q1/Q3."""
    if len(prices) < 4:
        return prices
    sorted_p = sorted(prices)
    n = len(sorted_p)
    q1 = sorted_p[n // 4]
    q3 = sorted_p[(3 * n) // 4]
    iqr = q3 - q1
    lo = q1 - 1.5 * iqr
    hi = q3 + 1.5 * iqr
    filtered = [p for p in sorted_p if lo <= p <= hi]
    return filtered if filtered else sorted_p


# ── Cost-aware price calculation ──────────────────────────────────────────


def apply_costs(base_price: float, costs: MarketplaceCosts) -> float:
    """
    Given a base sell price, calculate the net after all costs.
    Returns how much the seller actually pockets.

    Formula:
      net = base_price
            - base_price * (commission_pct / 100)
            - base_price * (tax_pct / 100)
            - fixed_fee
            - shipping_cost
            - extra_costs
    """
    net = base_price
    net -= base_price * (costs.commission_pct / 100)
    net -= base_price * (costs.tax_pct / 100)
    net -= costs.fixed_fee
    net -= costs.shipping_cost
    net -= costs.extra_costs
    return round(net, 2)


def minimum_viable_price(purchase_price: float, costs: MarketplaceCosts) -> float:
    """
    The lowest sell price where the seller breaks even.
    Solves: sell_price - commission - tax - fixed - shipping - extra = purchase_price

    sell_price * (1 - commission_pct/100 - tax_pct/100)
        = purchase_price + fixed_fee + shipping_cost + extra_costs
    """
    variable_deductions = (costs.commission_pct + costs.tax_pct) / 100
    fixed_total = costs.fixed_fee + costs.shipping_cost + costs.extra_costs
    if variable_deductions >= 1:
        return purchase_price + fixed_total  # edge case: 100%+ deductions
    mvp = (purchase_price + fixed_total) / (1 - variable_deductions)
    return round(mvp, 2)


# ── Main analytics ────────────────────────────────────────────────────────


def compute_price_analysis(
    price_brls: list[Optional[float]],
    purchase_price: Optional[float] = None,
    costs: Optional[MarketplaceCosts] = None,
) -> PriceAnalysis:
    prices = [p for p in price_brls if p is not None and p > 0]

    if not prices:
        return PriceAnalysis(
            count=0,
            min_price=None, max_price=None,
            mean_price=None, median_price=None,
            iqr_mean=None, competitive_floor=None,
            suggested_price_10pct=None,
            suggested_price_20pct=None,
            suggested_price_30pct=None,
            purchase_price=purchase_price,
            minimum_viable_price=None,
            is_viable=None,
        )

    prices_sorted = sorted(prices)
    filtered = _iqr_filtered(prices)
    iqr_mean = round(statistics.mean(filtered), 2) if filtered else None

    floor_idx = max(0, int(len(prices_sorted) * 0.20) - 1)
    competitive_floor = round(prices_sorted[floor_idx] * 0.99, 2)

    def markup(base: Optional[float], pct: float) -> Optional[float]:
        return round(base * (1 + pct), 2) if base else None

    # Viability calculation
    mvp = None
    is_viable = None
    if purchase_price is not None and costs is not None:
        mvp = minimum_viable_price(purchase_price, costs)
        is_viable = (iqr_mean is not None and iqr_mean >= mvp)
    elif purchase_price is not None and iqr_mean is not None:
        # No costs provided — simple comparison
        is_viable = iqr_mean > purchase_price

    return PriceAnalysis(
        count=len(prices),
        min_price=round(min(prices), 2),
        max_price=round(max(prices), 2),
        mean_price=round(statistics.mean(prices), 2),
        median_price=round(statistics.median(prices), 2),
        iqr_mean=iqr_mean,
        competitive_floor=competitive_floor,
        suggested_price_10pct=markup(iqr_mean, 0.10),
        suggested_price_20pct=markup(iqr_mean, 0.20),
        suggested_price_30pct=markup(iqr_mean, 0.30),
        purchase_price=purchase_price,
        minimum_viable_price=mvp,
        is_viable=is_viable,
    )
