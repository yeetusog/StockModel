# is this fetch worth saving
import pytest

from app.models.snapshot import PriceData, TechnicalIndicators
from app.services.quality import snapshot_quality


@pytest.mark.unit
def test_complete_when_price_and_indicators_present(live_price, live_tech):
    assert snapshot_quality(live_price, live_tech) == "complete"


@pytest.mark.unit
def test_empty_when_nothing_resolved(dead_ticker_data):
    price, tech = dead_ticker_data
    assert snapshot_quality(price, tech) == "empty"


@pytest.mark.unit
def test_partial_when_price_only(live_price):
    assert snapshot_quality(live_price, TechnicalIndicators()) == "partial"


@pytest.mark.unit
def test_partial_when_indicators_only(live_tech):
    assert snapshot_quality(PriceData(), live_tech) == "partial"


@pytest.mark.unit
def test_price_of_zero_is_still_data():
    """0.0 is a real price, not a missing one — must not be treated as empty."""
    assert snapshot_quality(PriceData(current=0.0), TechnicalIndicators()) == "partial"
