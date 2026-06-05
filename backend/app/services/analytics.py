"""
Price analytics engine.

All functions are pure (no DB or network calls) so they're easy to test
and swap out for an ML model later without touching the routes.
"""
import re
import statistics
from typing import Optional

from app.schemas.schemas import PriceAnalysis


# ── Price parsing ─────────────────────────────────────────────────────────


_PRICE_RE = re.compile(r"[\d.,]+")


def parse_price_brl(raw: Optional[str]) -> Optional[float]:
    """
    Extract the first numeric value from a scraped price string.

    Handles Brazilian formatting:
      "R$ 1.299,90"  → 1299.90
      "1299.90"      → 1299.90
      "1.299"        → 1299.0  (treated as BRL thousands separator)
    """
    if not raw:
        return None

    match = _PRICE_RE.search(raw)
    if not match:
        return None

    token = match.group()

    # Brazilian: "1.299,90" → remove dots, replace comma
    if "," in token and "." in token:
        token = token.replace(".", "").replace(",", ".")
    elif "," in token:
        # Could be "1299,90" or "1,299" — prefer decimal interpretation
        token = token.replace(",", ".")
    # else plain "1299.90" — leave as is

    try:
        value = float(token)
        # Sanity: reject clearly broken values
        if value <= 0 or value > 9_999_999:
            return None
        return round(value, 2)
    except ValueError:
        return None


# ── IQR filter ────────────────────────────────────────────────────────────


def _iqr_filtered(prices: list[float]) -> list[float]:
    """Remove outliers beyond 1.5 × IQR from Q1/Q3."""
    if len(prices) < 4:
        return prices  # not enough data to filter meaningfully

    sorted_p = sorted(prices)
    n = len(sorted_p)
    q1 = sorted_p[n // 4]
    q3 = sorted_p[(3 * n) // 4]
    iqr = q3 - q1
    lo = q1 - 1.5 * iqr
    hi = q3 + 1.5 * iqr
    filtered = [p for p in sorted_p if lo <= p <= hi]
    return filtered if filtered else sorted_p  # fallback if all filtered out


# ── Main analytics ────────────────────────────────────────────────────────


def compute_price_analysis(price_brls: list[Optional[float]]) -> PriceAnalysis:
    """
    Given a list of parsed prices (may contain None), return a PriceAnalysis.

    Args:
        price_brls: raw list from the results queryset, Nones allowed.

    Returns:
        PriceAnalysis with all computed fields.
    """
    prices = [p for p in price_brls if p is not None and p > 0]

    if not prices:
        return PriceAnalysis(
            count=0,
            min_price=None,
            max_price=None,
            mean_price=None,
            median_price=None,
            iqr_mean=None,
            competitive_floor=None,
            suggested_price_10pct=None,
            suggested_price_20pct=None,
            suggested_price_30pct=None,
        )

    prices_sorted = sorted(prices)
    filtered = _iqr_filtered(prices)
    iqr_mean = round(statistics.mean(filtered), 2) if filtered else None

    # competitive_floor = price just below the cheapest 20% of sellers
    floor_idx = max(0, int(len(prices_sorted) * 0.20) - 1)
    competitive_floor = round(prices_sorted[floor_idx] * 0.99, 2)

    def markup(base: Optional[float], pct: float) -> Optional[float]:
        return round(base * (1 + pct), 2) if base else None

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
    )
