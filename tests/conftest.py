import pytest
from fastapi.testclient import TestClient

from app.models.snapshot import NewsItem, PriceData, TechnicalIndicators


@pytest.fixture
def client():
    from main import app

    return TestClient(app)


@pytest.fixture
def live_price():
    return PriceData(current=313.33, close_prev=308.91, change_pct=1.43)


@pytest.fixture
def live_tech():
    return TechnicalIndicators(rsi_14=47.7, trend="bearish", volume_vs_avg_pct=-16.41)


@pytest.fixture
def dead_ticker_data():
    """What Yahoo returns for a ticker that does not resolve (APPL, TATAPOWER)."""
    return PriceData(), TechnicalIndicators()


@pytest.fixture
def patch_pipeline(monkeypatch):
    """
    Replace every network call in the refresh pipeline.
    Returns a dict the test mutates to control what each stage yields, plus
    a 'saved' list recording snapshots that reached storage.
    """
    state = {
        "price": PriceData(),
        "tech": TechnicalIndicators(),
        "yf_news": [],
        "g_news": [],
        "saved": [],
    }

    monkeypatch.setattr("app.routers.signal.fetch_price_data", lambda t: state["price"])
    monkeypatch.setattr("app.routers.signal.compute_technical_indicators", lambda t: state["tech"])
    monkeypatch.setattr("app.routers.signal.fetch_yfinance_news", lambda t, n=10: state["yf_news"])
    monkeypatch.setattr("app.routers.signal.fetch_google_news", lambda t: state["g_news"])
    monkeypatch.setattr("app.routers.signal.analyze_sentiment", lambda items: items)
    monkeypatch.setattr("app.routers.signal.save_snapshot", lambda s: state["saved"].append(s))

    return state


@pytest.fixture
def news_pair():
    """The real duplicate shape: Google appends ' - Publisher', Yahoo does not."""
    return [
        NewsItem(source="yfinance", title="Nike Stock Is Down 76% From Its High"),
        NewsItem(source="google", title="Nike Stock Is Down 76% From Its High - The Motley Fool"),
    ]
