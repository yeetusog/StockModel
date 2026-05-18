from pydantic import BaseModel, Field
from typing import Optional, List

class PriceData(BaseModel):
    current: Optional[float] = None
    open: Optional[float] = None
    high: Optional[float] = None
    low: Optional[float] = None
    close_prev: Optional[float] = None
    change_pct: Optional[float] = None
    volume: Optional[int] = None
    avg_volume_10d: Optional[int] = None
    market_cap: Optional[float] = None
    pe_ratio: Optional[float] = None
    eps: Optional[float] = None
    week_52_high: Optional[float] = None
    week_52_low: Optional[float] = None
    beta: Optional[float] = None
    dividend_yield: Optional[float] = None
    forward_pe: Optional[float] = None
    price_to_book: Optional[float] = None

class NewsItem(BaseModel):
    source: str
    title: str
    url: Optional[str] = None
    publisher: Optional[str] = None
    published_at: Optional[str] = None
    sentiment_score: Optional[float] = None
    sentiment_magnitude: Optional[float] = None
    sentiment_label: Optional[str] = None

class SentimentSummary(BaseModel):
    mean_score: Optional[float] = None
    magnitude_avg: Optional[float] = None
    positive_count: int = 0
    neutral_count: int = 0
    negative_count: int = 0
    label: Optional[str] = None

class TechnicalIndicators(BaseModel):
    rsi_14: Optional[float] = None
    rsi_signal: Optional[str] = None
    macd: Optional[float] = None
    macd_signal_line: Optional[float] = None
    macd_histogram: Optional[float] = None
    macd_crossover: Optional[str] = None
    sma_20: Optional[float] = None
    sma_50: Optional[float] = None
    ema_12: Optional[float] = None
    ema_26: Optional[float] = None
    bb_upper: Optional[float] = None
    bb_lower: Optional[float] = None
    bb_mid: Optional[float] = None
    bb_position: Optional[str] = None
    price_vs_sma20_pct: Optional[float] = None
    price_vs_sma50_pct: Optional[float] = None
    volume_vs_avg_pct: Optional[float] = None
    trend: Optional[str] = None

class LLMSignal(BaseModel):
    model_config = {"protected_namespaces": ()}

    signal: str
    confidence: Optional[str] = None
    rationale: List[str] = []
    model_used: Optional[str] = None
    generated_at: Optional[str] = None
    raw_response: Optional[str] = None

class MarketSnapshot(BaseModel):
    snapshot_id: str
    ticker: str
    timestamp: str
    refresh_type: str = "manual"
    price: PriceData = Field(default_factory=PriceData)
    technical: TechnicalIndicators = Field(default_factory=TechnicalIndicators)
    sentiment: SentimentSummary = Field(default_factory=SentimentSummary)
    news: List[NewsItem] = []
    llm_signal: Optional[LLMSignal] = None
    data_quality: dict = {}
