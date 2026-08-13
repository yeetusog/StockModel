# make sure the dedup fix stays fixed
import pytest

from app.models.snapshot import NewsItem
from app.services.news import dedupe_news


@pytest.mark.unit
def test_publisher_suffix_does_not_defeat_dedupe(news_pair):
    assert len(dedupe_news(news_pair)) == 1


@pytest.mark.unit
def test_keeps_the_bare_title(news_pair):
    """yfinance comes first and has no ' - Publisher' tail, so it should win."""
    assert dedupe_news(news_pair)[0].source == "yfinance"


@pytest.mark.unit
def test_distinct_stories_are_kept():
    items = [
        NewsItem(source="yfinance", title="Nike beats on earnings"),
        NewsItem(source="google", title="Apple announces new iPhone - Reuters"),
    ]
    assert len(dedupe_news(items)) == 2


@pytest.mark.unit
def test_empty_titles_do_not_collapse_into_one():
    items = [NewsItem(source="a", title=""), NewsItem(source="b", title="")]
    assert len(dedupe_news(items)) == 2


@pytest.mark.unit
def test_casing_and_punctuation_ignored():
    items = [
        NewsItem(source="yfinance", title="Nike Stock Is Down 76%!"),
        NewsItem(source="google", title="nike stock is down 76"),
    ]
    assert len(dedupe_news(items)) == 1
