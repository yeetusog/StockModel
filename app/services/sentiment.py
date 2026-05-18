# app/services/sentiment.py
import logging
from functools import lru_cache
from typing import List

from app.models.snapshot import NewsItem, SentimentSummary

logger = logging.getLogger(__name__)


@lru_cache(maxsize=1)
def _get_finbert_pipeline():
    """
    Load FinBERT once per process lifetime.
    Model: yiyanghkust/finbert-tone
    Labels emitted by pipeline: 'Positive', 'Negative', 'Neutral'
    top_k=None returns all three label scores per input (replaces deprecated return_all_scores=True).
    """
    from transformers import BertTokenizer, BertForSequenceClassification, pipeline

    model_name = "yiyanghkust/finbert-tone"
    tokenizer = BertTokenizer.from_pretrained(model_name)
    model = BertForSequenceClassification.from_pretrained(model_name, num_labels=3)
    return pipeline(
        "sentiment-analysis",
        model=model,
        tokenizer=tokenizer,
        top_k=None,          # returns all 3 label scores per input
    )


def _finbert_scores(texts: List[str]) -> List[float]:
    """
    Score a batch of texts with FinBERT.
    Returns a scalar per text: P(Positive) - P(Negative), range [-1, 1].
    Truncates each text to 512 tokens via the tokenizer's built-in limit.
    """
    if not texts:
        return []

    # Replace empty/None with a safe placeholder to keep index alignment
    safe_texts = [t[:1000] if t else "no title" for t in texts]

    try:
        nlp = _get_finbert_pipeline()
        results = nlp(safe_texts, truncation=True, max_length=512)
    except Exception as e:
        logger.error(f"FinBERT inference error: {e}")
        return [0.0] * len(texts)

    scores: List[float] = []
    for label_list in results:
        # label_list = [{"label": "Positive", "score": 0.92}, {"label": ...}, ...]
        prob_map = {item["label"].lower(): item["score"] for item in label_list}
        pos = prob_map.get("positive", 0.0)
        neg = prob_map.get("negative", 0.0)
        scores.append(round(pos - neg, 3))

    return scores


def analyze_sentiment(news_items: list[NewsItem]) -> list[NewsItem]:
    """
    Annotate each NewsItem in-place with FinBERT sentiment.
    Attaches: sentiment_score, sentiment_magnitude, sentiment_label.
    """
    if not news_items:
        return news_items

    texts = [item.title or "" for item in news_items]
    scores = _finbert_scores(texts)

    for item, score in zip(news_items, scores):
        item.sentiment_score = float(score)
        item.sentiment_magnitude = round(abs(score), 3)
        item.sentiment_label = (
            "positive" if score >= 0.2
            else "negative" if score <= -0.2
            else "neutral"
        )

    return news_items


def summarize_sentiment(news_items: list[NewsItem]) -> SentimentSummary:
    scores = [i.sentiment_score for i in news_items if i.sentiment_score is not None]
    if not scores:
        return SentimentSummary()

    mean = round(sum(scores) / len(scores), 3)
    mags = [i.sentiment_magnitude for i in news_items if i.sentiment_magnitude is not None]

    return SentimentSummary(
        mean_score=mean,
        magnitude_avg=round(sum(mags) / len(mags), 3) if mags else 0.0,
        positive_count=sum(1 for i in news_items if i.sentiment_label == "positive"),
        neutral_count=sum(1 for i in news_items if i.sentiment_label == "neutral"),
        negative_count=sum(1 for i in news_items if i.sentiment_label == "negative"),
        label=(
            "POSITIVE" if mean >= 0.2
            else "NEGATIVE" if mean <= -0.2
            else "NEUTRAL"
        ),
    )