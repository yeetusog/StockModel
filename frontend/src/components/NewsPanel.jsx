const signed = (value, digits = 2) => {
  if (value == null || Number.isNaN(Number(value))) return '—';
  const n = Number(value);
  return `${n >= 0 ? '+' : '-'}${Math.abs(n).toFixed(digits)}`;
};

export default function NewsPanel({ snapshot }) {
  const newsItems = snapshot?.news || [];

  return (
    <section className="panel">
      <div className="panel-head">
        <span className="panel-title">Latest News</span>
        <span className="panel-title">{newsItems.length} articles</span>
      </div>

      <div className="panel-body">
        {newsItems.length === 0 ? (
          <div className="empty-state">No articles loaded</div>
        ) : (
          <div className="news-list">
            {newsItems.map((item) => {
              const sentimentClass = item.sentiment_score >= 0.2 ? 'ns-pos' : item.sentiment_score <= -0.2 ? 'ns-neg' : 'ns-neu';
              const sourceClass = item.source === 'yfinance' ? 'ns-yf' : 'ns-go';
              const publishedText = item.published_at ? new Date(item.published_at).toLocaleDateString() : '';

              return (
                <div key={`${item.source}-${item.title}-${item.url}`} className="news-item">
                  <span className={`news-score ${sentimentClass}`}>{item.sentiment_score != null ? signed(item.sentiment_score, 2) : '—'}</span>
                  <span className={`news-src ${sourceClass}`}>{item.source}</span>
                  <div>
                    <div className="news-title">
                      {item.url ? (
                        <a href={item.url} target="_blank" rel="noreferrer noopener">{item.title || 'Untitled'}</a>
                      ) : (
                        item.title || 'Untitled'
                      )}
                    </div>
                    <div className="news-meta">{item.publisher || ''} {publishedText ? `· ${publishedText}` : ''}</div>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </section>
  );
}
