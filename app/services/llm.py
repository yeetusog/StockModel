import json
import logging
import math
import re
from datetime import datetime, timezone

from openai import OpenAI

from app.config import settings
from app.models.snapshot import LLMSignal, MarketSnapshot

logger = logging.getLogger(__name__)


def _fmt(value, spec: str = "") -> str:
    if value is None:
        return "N/A"
    try:
        if isinstance(value, float) and math.isnan(value):
            return "N/A"
        return f"{value:{spec}}" if spec else str(value)
    except (TypeError, ValueError):
        return str(value)


def _build_prompt(snap: MarketSnapshot) -> str:
    p, t, s = snap.price, snap.technical, snap.sentiment
    news_lines = "\n".join(
        f"  {i}. [{n.source.upper()}] {n.title} [score: {n.sentiment_score:+.2f}]"
        for i, n in enumerate(snap.news[:15], 1)
        if n.sentiment_score is not None
    )
    return f"""You are a professional quantitative equity analyst.
Analyze the following real-time data for {snap.ticker} and return ONLY valid JSON.

PRICE: ${_fmt(p.current)} | Change: {_fmt(p.change_pct, "+.2f")}% | 52W: ${_fmt(p.week_52_low)}-${_fmt(p.week_52_high)}
FUNDAMENTALS: P/E={_fmt(p.pe_ratio)} | EPS={_fmt(p.eps)} | Beta={_fmt(p.beta)} | MktCap=${_fmt(p.market_cap)}
TECHNICALS: Trend={_fmt(t.trend)} | RSI={_fmt(t.rsi_14)} ({_fmt(t.rsi_signal)}) | MACD={_fmt(t.macd_crossover)}
            SMA20=${_fmt(t.sma_20)} ({_fmt(t.price_vs_sma20_pct, "+.1f")}%) | SMA50=${_fmt(t.sma_50)} ({_fmt(t.price_vs_sma50_pct, "+.1f")}%)
            BB={_fmt(t.bb_position)} | Volume vs avg={_fmt(t.volume_vs_avg_pct, "+.1f")}%
SENTIMENT: {_fmt(s.label)} (mean={_fmt(s.mean_score, "+.3f")}) - {s.positive_count} pos / {s.neutral_count} neu / {s.negative_count} neg

NEWS HEADLINES:
{news_lines}

Respond ONLY with this JSON:
{{
  "signal": "BUY" or "SELL" or "HOLD",
  "confidence": "HIGH" or "MEDIUM" or "LOW",
  "rationale": ["technical reason", "sentiment/news reason", "risk/valuation note"]
}}"""


def get_llm_signal(snap: MarketSnapshot) -> LLMSignal:
    try:
        client = OpenAI(base_url=settings.nvidia_nim_base_url, api_key=settings.nvidia_api_key)
        response = client.chat.completions.create(
            model=settings.nvidia_nim_model,
            messages=[
                {"role": "system", "content": "You are a quantitative equity analyst. Return valid JSON only."},
                {"role": "user", "content": _build_prompt(snap)},
            ],
            temperature=0.1,
            max_tokens=512,
        )
        raw = response.choices[0].message.content.strip()
        match = re.search(r"\{.*?\}", raw, re.DOTALL)
        parsed = json.loads(match.group(0) if match else raw)
        signal = str(parsed.get("signal", "HOLD")).upper()
        if signal not in ("BUY", "SELL", "HOLD"):
            signal = "HOLD"
        return LLMSignal(
            signal=signal,
            confidence=parsed.get("confidence", "MEDIUM"),
            rationale=parsed.get("rationale", []),
            model_used=settings.nvidia_nim_model,
            generated_at=datetime.now(timezone.utc).isoformat(),
            raw_response=raw,
        )
    except Exception as e:
        logger.error(f"NIM API error: {e}")
        return LLMSignal(
            signal="HOLD",
            confidence="LOW",
            rationale=[f"Signal error: {e}", "Manual analysis required"],
            model_used=settings.nvidia_nim_model,
            generated_at=datetime.now(timezone.utc).isoformat(),
        )
