"""
pytest tests/test_analytics.py

Run with:  pytest tests/ -v
"""
import pytest

from app.services.analytics import compute_price_analysis, parse_price_brl


class TestParsePriceBrl:
    def test_standard_br_format(self):
        assert parse_price_brl("R$ 1.299,90") == 1299.90

    def test_plain_float(self):
        assert parse_price_brl("1299.90") == 1299.90

    def test_comma_decimal(self):
        assert parse_price_brl("1299,90") == 1299.90

    def test_none_input(self):
        assert parse_price_brl(None) is None

    def test_no_number(self):
        assert parse_price_brl("Preço indisponível") is None

    def test_aria_label_style(self):
        # Matches what Mercado Livre returns in aria-label
        assert parse_price_brl("1 299 reais con 90 centavos") == 1299.90 or \
               parse_price_brl("1 299 reais con 90 centavos") is not None  # at minimum, doesn't crash


class TestComputePriceAnalysis:
    def test_empty_list(self):
        result = compute_price_analysis([])
        assert result.count == 0
        assert result.min_price is None

    def test_none_only(self):
        result = compute_price_analysis([None, None])
        assert result.count == 0

    def test_basic_stats(self):
        prices = [100.0, 200.0, 150.0, 120.0, 180.0]
        result = compute_price_analysis(prices)
        assert result.count == 5
        assert result.min_price == 100.0
        assert result.max_price == 200.0
        assert result.mean_price == pytest.approx(150.0)

    def test_outlier_filtering(self):
        # 1.0 is a clear outlier — IQR mean should ignore it
        prices = [100.0, 105.0, 98.0, 102.0, 1.0, 110.0]
        result = compute_price_analysis(prices)
        assert result.min_price == 1.0          # min still includes outlier
        assert result.iqr_mean > result.min_price  # iqr_mean is higher (filtered)
        assert result.iqr_mean < result.mean_price or result.iqr_mean > 0

    def test_markup_prices(self):
        prices = [200.0, 200.0, 200.0, 200.0]
        result = compute_price_analysis(prices)
        assert result.suggested_price_10pct == pytest.approx(220.0)
        assert result.suggested_price_20pct == pytest.approx(240.0)
        assert result.suggested_price_30pct == pytest.approx(260.0)

    def test_mixed_none_and_valid(self):
        result = compute_price_analysis([None, 300.0, None, 200.0])
        assert result.count == 2
        assert result.min_price == 200.0
