# app/services/quality.py
from app.models.snapshot import PriceData, TechnicalIndicators

COMPLETE = "complete"
PARTIAL = "partial"
EMPTY = "empty"


def snapshot_quality(price: PriceData, technical: TechnicalIndicators) -> str:
    # how much of the fetch actually worked
    # (is not None, because a price of 0.0 is still a price)
    has_price = price.current is not None
    has_indicators = technical.rsi_14 is not None

    if not has_price and not has_indicators:
        return EMPTY
    if has_price and has_indicators:
        return COMPLETE
    return PARTIAL
