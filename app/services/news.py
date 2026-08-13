import yfinance as yf
import feedparser
import re
import urllib.parse
from curl_cffi import requests as curl_requests
from app.models.snapshot import NewsItem
import logging

logger = logging.getLogger(__name__)


def _dedupe_key(title: str) -> str:
    # google tacks on " - Publisher", yahoo doesn't
    text = title.rsplit(" - ", 1)[0] if " - " in title else title
    text = re.sub(r"[^a-z0-9 ]", "", text.lower())
    return re.sub(r"\s+", " ", text).strip()


def dedupe_news(items: list[NewsItem]) -> list[NewsItem]:
    # same story was getting scored twice
    seen: set[str] = set()
    unique: list[NewsItem] = []

    for item in items:
        key = _dedupe_key(item.title or "")
        if not key:
            unique.append(item)
            continue
        if key in seen:
            continue
        seen.add(key)
        unique.append(item)

    if len(unique) < len(items):
        logger.info(f"Deduped {len(items) - len(unique)} duplicate headline(s)")

    return unique

def _fetch_yahoo_search_news(ticker: str, limit: int = 10) -> list[NewsItem]:
    # yfinance news returns nothing now
    try:
        symbol = urllib.parse.quote(ticker, safe="")
        url = (
            f"https://query1.finance.yahoo.com/v1/finance/search"
            f"?q={symbol}&newsCount={limit}&quotesCount=0"
        )
        response = curl_requests.get(url, impersonate="chrome", timeout=15)
        response.raise_for_status()

        items = []
        for article in (response.json().get("news") or [])[:limit]:
            items.append(NewsItem(
                source="yfinance",
                title=article.get("title", ""),
                url=article.get("link", ""),
                publisher=article.get("publisher", ""),
                published_at=str(article.get("providerPublishTime", "")),
            ))
        return items
    except Exception as e:
        logger.warning(f"Yahoo search news fallback failed for {ticker}: {e}")
        return []

def fetch_yfinance_news(ticker: str, limit: int = 10) -> list[NewsItem]:
    try:
        t = yf.Ticker(ticker)
        items = []
        for article in (t.news or [])[:limit]:
            c = article.get("content", {})
            items.append(NewsItem(
                source="yfinance",
                title=c.get("title") or article.get("title", ""),
                url=c.get("canonicalUrl", {}).get("url") or article.get("link", ""),
                publisher=c.get("provider", {}).get("displayName") or article.get("publisher", ""),
                published_at=str(c.get("pubDate") or article.get("providerPublishTime", "")),
            ))
    except Exception as e:
        logger.error(f"yfinance news error: {e}")
        items = []

    return items or _fetch_yahoo_search_news(ticker, limit)

def fetch_google_news(ticker: str, company_name: str = "", limit: int = 10) -> list[NewsItem]:
    try:
        query_text = " ".join(part for part in (ticker, company_name, "stock") if part)
        query = urllib.parse.quote(query_text)
        url = f"https://news.google.com/rss/search?q={query}&hl=en-US&gl=US&ceid=US:en"
        feed = feedparser.parse(url)
        items = []
        for entry in feed.entries[:limit]:
            items.append(NewsItem(
                source="google",
                title=entry.get("title", ""),
                url=entry.get("link", ""),
                publisher=entry.get("source", {}).get("title", "Google News") if hasattr(entry, "source") else "Google News",
                published_at=getattr(entry, "published", ""),
            ))
        return items
    except Exception as e:
        logger.error(f"Google News error: {e}")
        return []
