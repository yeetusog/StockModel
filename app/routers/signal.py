# app/routers/signal.py
import asyncio
import logging
import re
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, Query

from app.config import settings
from app.models.snapshot import MarketSnapshot
from app.services.llm import get_llm_signal
from app.services.market import compute_technical_indicators, fetch_price_data
from app.services.news import dedupe_news, fetch_google_news, fetch_yfinance_news
from app.services.sentiment import analyze_sentiment, summarize_sentiment
from app.services.storage import load_history, load_latest_snapshot, save_snapshot

router = APIRouter()
logger = logging.getLogger(__name__)

TICKER_RE = re.compile(r"^[A-Z0-9]{1,10}(\.(NS|BO|L|TO|AX))?$")


def validate_ticker(ticker: str) -> str:
    t = ticker.strip().upper()
    if not TICKER_RE.match(t):
        raise HTTPException(status_code=422, detail=f"Invalid ticker: {ticker}")
    return t


def _snap_id(ticker: str) -> str:
    return f"{ticker}_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}"


@router.post("/refresh")
async def refresh_data(ticker: str = Query(default=None)):
    """
    Fetch live price, technicals, news, and run FinBERT sentiment.
    Does NOT call the LLM — use POST /signal for that.
    """
    ticker = validate_ticker(ticker or settings.ticker)
    news_ticker = ticker.split(".")[0]
    logger.info(f"[refresh] Starting data refresh for {ticker}")
    loop = asyncio.get_event_loop()

    price, tech, yf_news, g_news = await asyncio.gather(
        loop.run_in_executor(None, fetch_price_data, ticker),
        loop.run_in_executor(None, compute_technical_indicators, ticker),
        loop.run_in_executor(None, fetch_yfinance_news, ticker, 10),
        loop.run_in_executor(None, fetch_google_news, news_ticker),
    )

    # drop repeats before scoring
    unique_news = dedupe_news(yf_news + g_news)
    all_news = await loop.run_in_executor(None, analyze_sentiment, unique_news)
    sentiment = summarize_sentiment(all_news)

    snap = MarketSnapshot(
        snapshot_id=_snap_id(ticker),
        ticker=ticker,
        timestamp=datetime.now(timezone.utc).isoformat(),
        price=price,
        technical=tech,
        news=all_news,
        sentiment=sentiment,
        data_quality={
            "price_available": price.current is not None,
            "news_count": len(all_news),
            "yfinance_news": len(yf_news),
            "google_news": len(g_news),
            "indicators_available": tech.rsi_14 is not None,
            "sentiment_method": "finbert",
        },
    )

    await loop.run_in_executor(None, save_snapshot, snap)
    logger.info(f"[refresh] Completed for {ticker} — {len(all_news)} articles, sentiment={sentiment.label}")

    return {
        "status": "success",
        "snapshot_id": snap.snapshot_id,
        "ticker": ticker,
        "timestamp": snap.timestamp,
        "price": snap.price.current,
        "change_pct": snap.price.change_pct,
        "trend": snap.technical.trend,
        "sentiment": snap.sentiment.label,
        "news_count": len(all_news),
        "data_quality": snap.data_quality,
    }


@router.post("/signal")
async def get_signal(ticker: str = Query(default=None)):
    """
    Load latest snapshot and call NVIDIA NIM for BUY / SELL / HOLD.
    Requires POST /refresh to have been called first.
    """
    ticker = validate_ticker(ticker or settings.ticker)

    if not settings.nvidia_api_key:
        raise HTTPException(status_code=400, detail="NVIDIA_API_KEY not set in .env")

    snap = load_latest_snapshot(ticker)
    if not snap:
        raise HTTPException(
            status_code=404,
            detail=f"No snapshot found for {ticker}. Run POST /refresh first.",
        )

    loop = asyncio.get_event_loop()
    sig = await loop.run_in_executor(None, get_llm_signal, snap)
    snap.llm_signal = sig
    await loop.run_in_executor(None, save_snapshot, snap)

    logger.info(f"[signal] {ticker} → {sig.signal} ({sig.confidence})")

    return {
        "status": "success",
        "ticker": ticker,
        "signal": sig.signal,
        "confidence": sig.confidence,
        "rationale": sig.rationale,
        "model_used": sig.model_used,
        "model": sig.model_used,
        "generated_at": sig.generated_at,
        "snapshot_id": snap.snapshot_id,
    }


@router.get("/data/latest")
async def get_latest(ticker: str = Query(default=None)):
    """
    Return full snapshot JSON.
    Primary read target for MCP server.
    """
    ticker = validate_ticker(ticker or settings.ticker)
    snap = load_latest_snapshot(ticker)
    if not snap:
        raise HTTPException(
            status_code=404,
            detail=f"No data for {ticker}. Run POST /refresh first.",
        )
    return snap.model_dump()


@router.get("/history")
async def get_history(ticker: str = Query(default=None), limit: int = Query(default=20)):
    """Return last N archived snapshots for a ticker."""
    ticker = validate_ticker(ticker or settings.ticker)
    records = load_history(ticker, limit)
    return {
        "ticker": ticker,
        "count": len(records),
        "history": records,
    }
