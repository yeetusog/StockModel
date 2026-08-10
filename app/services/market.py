import logging
import math
import urllib.parse

import pandas as pd
import pandas_ta as ta
import yfinance as yf
from curl_cffi import requests as curl_requests

from app.models.snapshot import PriceData, TechnicalIndicators

logger = logging.getLogger(__name__)


def _clean_number(value):
    if value is None:
        return None
    try:
        value = float(value)
    except (TypeError, ValueError):
        return None
    return None if math.isnan(value) else value


def _round_or_none(value, digits: int = 2):
    value = _clean_number(value)
    return round(value, digits) if value is not None else None


def _last_valid(series):
    if series is None:
        return None
    valid = series.dropna()
    if valid.empty:
        return None
    return _clean_number(valid.iloc[-1])


def _fetch_chart(ticker: str, range_: str = "5d", interval: str = "1d") -> tuple[dict, pd.DataFrame]:
    symbol = urllib.parse.quote(ticker, safe="")
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}?range={range_}&interval={interval}"
    response = curl_requests.get(url, impersonate="chrome", timeout=20)
    response.raise_for_status()

    payload = response.json()
    result = (payload.get("chart", {}).get("result") or [None])[0]
    if not result:
        return {}, pd.DataFrame()

    quote = (result.get("indicators", {}).get("quote") or [{}])[0]
    timestamps = result.get("timestamp") or []
    df = pd.DataFrame(
        {
            "Open": quote.get("open") or [],
            "High": quote.get("high") or [],
            "Low": quote.get("low") or [],
            "Close": quote.get("close") or [],
            "Volume": quote.get("volume") or [],
        },
        index=pd.to_datetime(timestamps, unit="s", utc=True) if timestamps else None,
    )
    if not df.empty:
        df = df.dropna(subset=["Close"], how="all")

    return result.get("meta", {}) or {}, df


def _yf_info(ticker_obj, ticker: str) -> dict:
    try:
        return ticker_obj.info or {}
    except Exception as e:
        logger.warning(f"yfinance info fallback for {ticker}: {e}")
        return {}


def _yf_fast_info(ticker_obj, ticker: str):
    try:
        return ticker_obj.fast_info
    except Exception as e:
        logger.warning(f"yfinance fast_info fallback for {ticker}: {e}")
        return None


def _fast_get(fast, name: str):
    if fast is None:
        return None
    try:
        return getattr(fast, name, None)
    except Exception:
        return None


def _fetch_quote_summary(ticker: str) -> dict:
    try:
        base = "https://query2.finance.yahoo.com/v10/finance/quoteSummary/"
        modules = "summaryDetail,defaultKeyStatistics,financialData,price"
        url = (
            f"{base}{urllib.parse.quote(ticker, safe='')}"
            f"?modules={modules}&corsDomain=finance.yahoo.com"
        )
        resp = curl_requests.get(url, impersonate="chrome", timeout=12)
        if resp.status_code == 401:
            session = curl_requests.Session(impersonate="chrome")
            session.get("https://fc.yahoo.com", timeout=12)
            crumb = session.get("https://query1.finance.yahoo.com/v1/test/getcrumb", timeout=12).text.strip()
            resp = session.get(f"{url}&crumb={urllib.parse.quote(crumb, safe='')}", timeout=12)
        resp.raise_for_status()

        result = resp.json().get("quoteSummary", {}).get("result") or []
        if not result:
            return {}
        data = result[0]
        sd = data.get("summaryDetail", {})
        ks = data.get("defaultKeyStatistics", {})
        pr = data.get("price", {})

        return {
            # yfinance stopped returning these three
            "market_cap": _clean_number((pr.get("marketCap") or {}).get("raw")),
            "open": _clean_number((sd.get("open") or {}).get("raw")),
            "avg_volume_10d": _clean_number((sd.get("averageDailyVolume10Day") or {}).get("raw")),
            "pe_ratio": _clean_number((sd.get("trailingPE") or {}).get("raw")),
            "forward_pe": _clean_number((sd.get("forwardPE") or {}).get("raw")),
            "eps": _clean_number((ks.get("trailingEps") or {}).get("raw")),
            "beta": _clean_number((ks.get("beta") or {}).get("raw")),
            "dividend_yield": _clean_number(((sd.get("dividendYield") or {}).get("raw"))),
            "price_to_book": _clean_number((ks.get("priceToBook") or {}).get("raw")),
            "week_52_high": _clean_number((sd.get("fiftyTwoWeekHigh") or {}).get("raw")),
            "week_52_low": _clean_number((sd.get("fiftyTwoWeekLow") or {}).get("raw")),
        }
    except Exception as e:
        logger.warning(f"Yahoo quoteSummary fallback failed for {ticker}: {e}")
        return {}


def _fetch_volume_vs_avg(ticker: str, current_volume: int | None) -> float | None:
    try:
        _, df = _fetch_chart(ticker, range_="1mo", interval="1d")
        volume_series = df["Volume"].dropna()
        if len(volume_series) < 5:
            return None
        avg_vol = float(volume_series.iloc[:-1].mean())
        cur_vol = current_volume if current_volume is not None else float(volume_series.iloc[-1])
        if avg_vol == 0:
            return None
        return round((cur_vol / avg_vol - 1) * 100, 2)
    except Exception:
        return None


def fetch_price_data(ticker: str) -> PriceData:
    try:
        t = yf.Ticker(ticker)
        info = _yf_info(t, ticker)
        fast = _yf_fast_info(t, ticker)

        try:
            meta, chart = _fetch_chart(ticker)
        except Exception as e:
            logger.warning(f"Yahoo chart fallback failed for {ticker}: {e}")
            meta, chart = {}, pd.DataFrame()

        current = (
            _clean_number(_fast_get(fast, "last_price"))
            or _clean_number(info.get("currentPrice"))
            or _clean_number(meta.get("regularMarketPrice"))
        )
        if current is None and not chart.empty:
            current = _last_valid(chart["Close"])

        prev_close = (
            _clean_number(_fast_get(fast, "previous_close"))
            or _clean_number(info.get("previousClose"))
            or _clean_number(meta.get("chartPreviousClose"))
        )
        if prev_close is None and not chart.empty:
            closes = chart["Close"].dropna()
            if len(closes) > 1:
                prev_close = _clean_number(closes.iloc[-2])

        change_pct = None
        if current is not None and prev_close not in (None, 0):
            change_pct = round(((current - prev_close) / prev_close) * 100, 2)

        volume = meta.get("regularMarketVolume") or info.get("volume")
        qs = _fetch_quote_summary(ticker)

        avg_vol_10d = info.get("averageVolume10days") or qs.get("avg_volume_10d")

        return PriceData(
            current=_round_or_none(current),
            open=_clean_number(
                info.get("open") or info.get("regularMarketOpen")
                or meta.get("regularMarketOpen") or qs.get("open")
            ),
            high=_clean_number(_fast_get(fast, "day_high") or meta.get("regularMarketDayHigh")),
            low=_clean_number(_fast_get(fast, "day_low") or meta.get("regularMarketDayLow")),
            close_prev=_round_or_none(prev_close),
            change_pct=change_pct,
            volume=int(volume) if volume else None,
            avg_volume_10d=int(avg_vol_10d) if avg_vol_10d else None,
            market_cap=_clean_number(
                _fast_get(fast, "market_cap") or info.get("marketCap") or qs.get("market_cap")
            ),
            pe_ratio=qs.get("pe_ratio"),
            eps=qs.get("eps"),
            week_52_high=qs.get("week_52_high") or _clean_number(_fast_get(fast, "year_high")),
            week_52_low=qs.get("week_52_low") or _clean_number(_fast_get(fast, "year_low")),
            beta=qs.get("beta"),
            dividend_yield=qs.get("dividend_yield"),
            forward_pe=qs.get("forward_pe"),
            price_to_book=qs.get("price_to_book"),
        )
    except Exception as e:
        logger.error(f"Price fetch error: {e}")
        return PriceData()


def _history_with_fallback(ticker: str) -> pd.DataFrame:
    t = yf.Ticker(ticker)
    try:
        df = t.history(period="5d", interval="1m")
    except Exception as e:
        logger.warning(f"yfinance 1m history fallback for {ticker}: {e}")
        df = pd.DataFrame()
    if df.empty or len(df) < 30:
        try:
            _, df = _fetch_chart(ticker, "5d", "1m")
        except Exception as e:
            logger.warning(f"Yahoo chart 1m fallback failed for {ticker}: {e}")
            df = pd.DataFrame()

    if df.empty or len(df) < 30:
        try:
            df = t.history(period="3mo", interval="1d")
        except Exception as e:
            logger.warning(f"yfinance daily history fallback for {ticker}: {e}")
            df = pd.DataFrame()
    if df.empty or len(df) < 30:
        try:
            _, df = _fetch_chart(ticker, "3mo", "1d")
        except Exception as e:
            logger.warning(f"Yahoo chart daily fallback failed for {ticker}: {e}")
            df = pd.DataFrame()

    return df


def compute_technical_indicators(ticker: str) -> TechnicalIndicators:
    try:
        df = _history_with_fallback(ticker)
        if df.empty:
            return TechnicalIndicators()

        close = df["Close"].dropna()
        if close.empty:
            return TechnicalIndicators()
        current_price = float(close.iloc[-1])

        rsi_s = ta.rsi(close, length=14)
        rsi_val = _round_or_none(_last_valid(rsi_s), 2)
        rsi_signal = (
            "overbought" if rsi_val is not None and rsi_val >= 70
            else "oversold" if rsi_val is not None and rsi_val <= 30
            else "neutral" if rsi_val is not None
            else None
        )

        macd_df = ta.macd(close, fast=12, slow=26, signal=9)
        macd_val = macd_sig = macd_hist = macd_cross = None
        if macd_df is not None and not macd_df.dropna(how="all").empty:
            macd_df = macd_df.dropna(how="all")
            macd_col = next((c for c in macd_df.columns if c.startswith("MACD_")), macd_df.columns[0])
            hist_col = next((c for c in macd_df.columns if c.startswith("MACDh_")), macd_df.columns[-1])
            sig_col = next((c for c in macd_df.columns if c.startswith("MACDs_")), macd_df.columns[1])
            macd_val = _round_or_none(_last_valid(macd_df[macd_col]), 4)
            macd_sig = _round_or_none(_last_valid(macd_df[sig_col]), 4)
            macd_hist = _round_or_none(_last_valid(macd_df[hist_col]), 4)
            hist_valid = macd_df[hist_col].dropna()
            prev_h = float(hist_valid.iloc[-2]) if len(hist_valid) > 1 else 0
            if macd_hist is not None:
                macd_cross = (
                    "bullish_crossover" if macd_hist > 0 and prev_h <= 0
                    else "bearish_crossover" if macd_hist < 0 and prev_h >= 0
                    else "bullish" if macd_hist > 0
                    else "bearish"
                )

        sma20 = ta.sma(close, length=20)
        sma50 = ta.sma(close, length=50)
        ema12 = ta.ema(close, length=12)
        ema26 = ta.ema(close, length=26)
        sma20_v = _round_or_none(_last_valid(sma20), 2)
        sma50_v = _round_or_none(_last_valid(sma50), 2)

        bb = ta.bbands(close, length=20, std=2)
        bb_upper = bb_lower = bb_mid = bb_pos = None
        if bb is not None and not bb.dropna(how="all").empty:
            bb = bb.dropna(how="all")
            lower_col = next((c for c in bb.columns if c.startswith("BBL_")), bb.columns[0])
            mid_col = next((c for c in bb.columns if c.startswith("BBM_")), bb.columns[1])
            upper_col = next((c for c in bb.columns if c.startswith("BBU_")), bb.columns[2])
            bb_lower = _round_or_none(_last_valid(bb[lower_col]), 2)
            bb_mid = _round_or_none(_last_valid(bb[mid_col]), 2)
            bb_upper = _round_or_none(_last_valid(bb[upper_col]), 2)
            if bb_upper is not None and bb_lower is not None and bb_upper != bb_lower:
                pctb = (current_price - bb_lower) / (bb_upper - bb_lower)
                bb_pos = "near_upper" if pctb > 0.8 else "near_lower" if pctb < 0.2 else "middle"

        p_vs_20 = round(((current_price - sma20_v) / sma20_v) * 100, 2) if sma20_v else None
        p_vs_50 = round(((current_price - sma50_v) / sma50_v) * 100, 2) if sma50_v else None

        # minute bars pinned this at -100%
        vol_pct = _fetch_volume_vs_avg(ticker, None)

        trend = (
            "bullish" if sma20_v and sma50_v and current_price > sma20_v > sma50_v
            else "bearish" if sma20_v and sma50_v and current_price < sma20_v < sma50_v
            else "neutral"
        )

        return TechnicalIndicators(
            rsi_14=rsi_val,
            rsi_signal=rsi_signal,
            macd=macd_val,
            macd_signal_line=macd_sig,
            macd_histogram=macd_hist,
            macd_crossover=macd_cross,
            sma_20=sma20_v,
            sma_50=sma50_v,
            ema_12=_round_or_none(_last_valid(ema12), 2),
            ema_26=_round_or_none(_last_valid(ema26), 2),
            bb_upper=bb_upper,
            bb_lower=bb_lower,
            bb_mid=bb_mid,
            bb_position=bb_pos,
            price_vs_sma20_pct=p_vs_20,
            price_vs_sma50_pct=p_vs_50,
            volume_vs_avg_pct=vol_pct,
            trend=trend,
        )
    except Exception as e:
        logger.error(f"Indicators error: {e}")
        return TechnicalIndicators()
