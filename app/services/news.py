import yfinance as yf
import feedparser
import urllib.parse
from app.models.snapshot import NewsItem
import logging

logger = logging.getLogger(__name__)

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
        return items
    except Exception as e:
        logger.error(f"yfinance news error: {e}")
        return []

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
