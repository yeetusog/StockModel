const formatNumber = (value, digits = 2) => {
  if (value == null || Number.isNaN(Number(value))) return '—';
  return Number(value).toFixed(digits);
};

const signed = (value, digits = 2) => {
  if (value == null || Number.isNaN(Number(value))) return '—';
  const n = Number(value);
  return `${n >= 0 ? '+' : '-'}${Math.abs(n).toFixed(digits)}`;
};

export default function TechnicalPanel({ snapshot }) {
  const technical = snapshot?.technical || {};

  const rsi = technical.rsi_14;
  const rsiClass = rsi >= 70 ? 'down' : rsi <= 30 ? 'up' : 'flat';
  const rsiPercent = rsi != null ? Math.min(Math.max(Number(rsi), 0), 100) : 50;

  const macdBullish = (technical.macd_crossover || '').includes('bull');

  const trend = (technical.trend || '').toLowerCase();
  const trendColor = trend === 'bullish' ? 'up' : trend === 'bearish' ? 'down' : 'flat';

  return (
    <section className="panel">
      <div className="panel-head">
        <span className="panel-title">Technical Indicators</span>
        <span className={`trend-tag ${trendColor}`}>{technical.trend || '—'}</span>
      </div>

      <div className="panel-body">
        <div className="tech-grid">
          <div className="tech-tile">
            <div className="tech-label">RSI (14)</div>
            <div className={`tech-val ${rsiClass}`}>{rsi != null ? formatNumber(rsi, 1) : '—'}</div>
            <div className={`tech-sub ${rsiClass}`}>{technical.rsi_signal || '—'}</div>
            <div className="rsi-track">
              <div
                className="rsi-fill"
                style={{
                  width: `${rsiPercent}%`,
                  background: rsi >= 70 ? 'var(--sell)' : rsi <= 30 ? 'var(--buy)' : 'var(--hold)',
                }}
              />
              <div className="rsi-pin" style={{ left: `${rsiPercent}%` }} />
            </div>
          </div>

          <div className="tech-tile">
            <div className="tech-label">MACD</div>
            <div className={`tech-val ${macdBullish ? 'up' : 'down'}`}>{technical.macd != null ? formatNumber(technical.macd, 4) : '—'}</div>
            <div className={`tech-sub ${macdBullish ? 'up' : 'down'}`}>{technical.macd_crossover || '—'}</div>
          </div>

          <div className="tech-tile">
            <div className="tech-label">SMA 20</div>
            <div className="tech-val">{technical.sma_20 != null ? `$${formatNumber(technical.sma_20)}` : '—'}</div>
            <div className={`tech-sub ${technical.price_vs_sma20_pct > 0 ? 'up' : technical.price_vs_sma20_pct < 0 ? 'down' : 'flat'}`}>
              {technical.price_vs_sma20_pct != null ? `${signed(technical.price_vs_sma20_pct, 1)}% vs price` : '—'}
            </div>
          </div>

          <div className="tech-tile">
            <div className="tech-label">SMA 50</div>
            <div className="tech-val">{technical.sma_50 != null ? `$${formatNumber(technical.sma_50)}` : '—'}</div>
            <div className={`tech-sub ${technical.price_vs_sma50_pct > 0 ? 'up' : technical.price_vs_sma50_pct < 0 ? 'down' : 'flat'}`}>
              {technical.price_vs_sma50_pct != null ? `${signed(technical.price_vs_sma50_pct, 1)}% vs price` : '—'}
            </div>
          </div>

          <div className="tech-tile">
            <div className="tech-label">Bollinger</div>
            <div className="tech-val">{technical.bb_lower != null && technical.bb_upper != null ? `$${formatNumber(technical.bb_lower)}–$${formatNumber(technical.bb_upper)}` : '—'}</div>
            <div className={`tech-sub ${technical.bb_position === 'near_upper' ? 'down' : technical.bb_position === 'near_lower' ? 'up' : 'flat'}`}>
              {technical.bb_position || '—'}
            </div>
          </div>

          <div className="tech-tile">
            <div className="tech-label">Vol vs Avg</div>
            <div className={`tech-val ${technical.volume_vs_avg_pct > 20 ? 'up' : technical.volume_vs_avg_pct < -20 ? 'down' : 'flat'}`}>
              {technical.volume_vs_avg_pct != null ? `${signed(technical.volume_vs_avg_pct, 1)}%` : '—'}
            </div>
            <div className="tech-sub">20-day avg</div>
          </div>
        </div>
      </div>
    </section>
  );
}
