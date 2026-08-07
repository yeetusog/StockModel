const signed = (value, digits = 2) => {
  if (value == null || Number.isNaN(Number(value))) return '—';
  const n = Number(value);
  return `${n >= 0 ? '+' : '-'}${Math.abs(n).toFixed(digits)}`;
};

export default function SentimentPanel({ snapshot }) {
  const sentiment = snapshot?.sentiment || {};
  const total = (sentiment.positive_count || 0) + (sentiment.neutral_count || 0) + (sentiment.negative_count || 0);
  const score = sentiment.mean_score;
  const scoreClass = score >= 0.2 ? 'up' : score <= -0.2 ? 'down' : 'flat';

  return (
    <section className="panel">
      <div className="panel-head">
        <span className="panel-title">News Sentiment</span>
        <span className="panel-title">{snapshot?.data_quality?.sentiment_method || '—'}</span>
      </div>

      <div className="panel-body">
        <div className={`sent-score ${scoreClass}`}>{score != null ? signed(score, 3) : '—'}</div>
        <div className={`sent-label ${scoreClass}`}>{sentiment.label || 'NO DATA'}</div>

        <div className="sent-bar">
          <div className="sb-pos" style={{ width: total ? `${((sentiment.positive_count || 0) / total) * 100}%` : '33%' }} />
          <div className="sb-neu" style={{ width: total ? `${((sentiment.neutral_count || 0) / total) * 100}%` : '34%' }} />
          <div className="sb-neg" style={{ width: total ? `${((sentiment.negative_count || 0) / total) * 100}%` : '33%' }} />
        </div>

        <div className="sent-counts">
          <span><span className="up">{sentiment.positive_count || 0}</span> Positive</span>
          <span><span className="flat">{sentiment.neutral_count || 0}</span> Neutral</span>
          <span><span className="down">{sentiment.negative_count || 0}</span> Negative</span>
        </div>
      </div>
    </section>
  );
}
