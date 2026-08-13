# empty fetches shouldn't look like wins
import pytest

from app.models.snapshot import NewsItem


@pytest.mark.integration
def test_dead_ticker_is_rejected(client, patch_pipeline):
    """APPL / TATAPOWER resolve to nothing — that is an error, not a success."""
    response = client.post("/refresh?ticker=APPL")
    assert response.status_code == 502


@pytest.mark.integration
def test_dead_ticker_saves_nothing(client, patch_pipeline):
    """The bug this fixes: an all-null snapshot used to land in data/snapshots."""
    client.post("/refresh?ticker=APPL")
    assert patch_pipeline["saved"] == []


@pytest.mark.integration
def test_live_ticker_still_succeeds(client, patch_pipeline, live_price, live_tech):
    patch_pipeline["price"] = live_price
    patch_pipeline["tech"] = live_tech

    response = client.post("/refresh?ticker=AAPL")

    assert response.status_code == 200
    assert response.json()["status"] == "success"
    assert len(patch_pipeline["saved"]) == 1


@pytest.mark.integration
def test_partial_fetch_is_reported_as_partial(client, patch_pipeline, live_price):
    """Price came back but indicators did not — saved, but not called a success."""
    patch_pipeline["price"] = live_price

    response = client.post("/refresh?ticker=AAPL")

    assert response.status_code == 200
    assert response.json()["status"] == "partial"
    assert len(patch_pipeline["saved"]) == 1


@pytest.mark.integration
def test_duplicate_headlines_dropped_before_save(client, patch_pipeline, live_price, live_tech, news_pair):
    patch_pipeline["price"] = live_price
    patch_pipeline["tech"] = live_tech
    patch_pipeline["yf_news"] = [news_pair[0]]
    patch_pipeline["g_news"] = [news_pair[1]]

    response = client.post("/refresh?ticker=NKE")

    assert response.json()["news_count"] == 1


@pytest.mark.integration
def test_invalid_ticker_format_still_422(client, patch_pipeline):
    """Existing validation behaviour must not regress."""
    assert client.post("/refresh?ticker=not a ticker!").status_code == 422
