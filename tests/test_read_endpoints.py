# the read routes people actually call
import pytest

from app.models.snapshot import MarketSnapshot, PriceData


@pytest.fixture
def stored_snapshot():
    return MarketSnapshot(
        snapshot_id="AAPL_20260810_120000",
        ticker="AAPL",
        timestamp="2026-08-10T12:00:00+00:00",
        price=PriceData(current=313.33),
    )


@pytest.mark.integration
def test_latest_returns_snapshot(client, monkeypatch, stored_snapshot):
    monkeypatch.setattr("app.routers.signal.load_latest_snapshot", lambda t: stored_snapshot)

    response = client.get("/data/latest?ticker=AAPL")

    assert response.status_code == 200
    assert response.json()["price"]["current"] == 313.33


@pytest.mark.integration
def test_latest_404s_when_never_refreshed(client, monkeypatch):
    monkeypatch.setattr("app.routers.signal.load_latest_snapshot", lambda t: None)
    assert client.get("/data/latest?ticker=AAPL").status_code == 404


@pytest.mark.integration
def test_history_returns_count(client, monkeypatch):
    monkeypatch.setattr("app.routers.signal.load_history", lambda t, n: [{"ticker": "AAPL"}])

    body = client.get("/history?ticker=AAPL&limit=5").json()

    assert body["count"] == 1
    assert body["ticker"] == "AAPL"


@pytest.mark.integration
def test_history_empty_is_not_an_error(client, monkeypatch):
    monkeypatch.setattr("app.routers.signal.load_history", lambda t, n: [])

    response = client.get("/history?ticker=AAPL")

    assert response.status_code == 200
    assert response.json()["count"] == 0


@pytest.mark.integration
def test_signal_requires_api_key(client, monkeypatch):
    monkeypatch.setattr("app.routers.signal.settings.nvidia_api_key", "")
    assert client.post("/signal?ticker=AAPL").status_code == 400


@pytest.mark.integration
def test_signal_needs_a_refresh_first(client, monkeypatch):
    monkeypatch.setattr("app.routers.signal.settings.nvidia_api_key", "key")
    monkeypatch.setattr("app.routers.signal.load_latest_snapshot", lambda t: None)
    assert client.post("/signal?ticker=AAPL").status_code == 404


@pytest.mark.integration
def test_health_reports_key_state(client):
    body = client.get("/health").json()
    assert body["status"] == "ok"
    assert "nim_key_set" in body


@pytest.mark.integration
@pytest.mark.parametrize("ticker", ["AAPL", "BEL.NS", "ICICIBANK.NS"])
def test_valid_ticker_formats_accepted(client, monkeypatch, ticker, stored_snapshot):
    monkeypatch.setattr("app.routers.signal.load_latest_snapshot", lambda t: stored_snapshot)
    assert client.get(f"/data/latest?ticker={ticker}").status_code == 200


@pytest.mark.integration
@pytest.mark.parametrize("ticker", ["not a ticker!", "TOOLONGTICKERNAME", "AAPL.XX"])
def test_malformed_tickers_rejected(client, ticker):
    assert client.get(f"/data/latest?ticker={ticker}").status_code == 422
