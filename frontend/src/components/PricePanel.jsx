const formatNumber = (value, digits = 2) => {
  if (value == null || Number.isNaN(Number(value))) return '—';
  return Number(value).toFixed(digits);
};

const formatSigned = (value, digits = 2) => {
  if (value == null || Number.isNaN(Number(value))) return '—';
  const n = Number(value);
  return `${n >= 0 ? '+' : '-'}${Math.abs(n).toFixed(digits)}`;
};

const formatCompactMoney = (value) => {
  if (value == null || Number.isNaN(Number(value))) return '—';
  const number = Number(value);

  if (number >= 1e12) return `$${(number / 1e12).toFixed(2)}T`;
  if (number >= 1e9) return `$${(number / 1e9).toFixed(2)}B`;
  if (number >= 1e6) return `$${(number / 1e6).toFixed(2)}M`;
  return `$${number.toLocaleString()}`;
};

export default function PricePanel({ snapshot }) {
  const price = snapshot?.price || {};
  const timestamp = snapshot?.timestamp ? new Date(snapshot.timestamp).toLocaleTimeString() : '—';

  const priceValue = price.current != null ? `$${formatNumber(price.current, 2)}` : '—';
  const changePercent = price.change_pct != null ? Number(price.change_pct) : null;
  const moveClass = changePercent > 0 ? 'up' : changePercent < 0 ? 'down' : 'flat';

  return (
    <section className="panel">
      <div className="panel-head">
        <span className="panel-title">Live Price</span>
        <span className="panel-title">{timestamp}</span>
      </div>

      <div className="price-hero">
        <div className="price-top">
          <div>
            <div className="price-number">{priceValue}</div>
            <div className={`price-change ${moveClass}`}>
              {changePercent != null ? `${changePercent >= 0 ? '+' : '-'}$${formatNumber(Math.abs(Number(price.current) - Number(price.close_prev || 0)), 2)} (${formatSigned(changePercent, 2)}%)` : '—'}
            </div>
          </div>
          <div className="badge-mktcap">Mkt Cap {formatCompactMoney(price.market_cap)}</div>
        </div>

        <div className="price-grid">
          <div className="pstat"><div className="pstat-label">Open</div><div className="pstat-value">{price.open != null ? `$${formatNumber(price.open)}` : '—'}</div></div>
          <div className="pstat"><div className="pstat-label">High</div><div className="pstat-value">{price.high != null ? `$${formatNumber(price.high)}` : '—'}</div></div>
          <div className="pstat"><div className="pstat-label">Low</div><div className="pstat-value">{price.low != null ? `$${formatNumber(price.low)}` : '—'}</div></div>
          <div className="pstat"><div className="pstat-label">Prev Close</div><div className="pstat-value">{price.close_prev != null ? `$${formatNumber(price.close_prev)}` : '—'}</div></div>
          <div className="pstat"><div className="pstat-label">52W High</div><div className="pstat-value">{price.week_52_high != null ? `$${formatNumber(price.week_52_high)}` : '—'}</div></div>
          <div className="pstat"><div className="pstat-label">52W Low</div><div className="pstat-value">{price.week_52_low != null ? `$${formatNumber(price.week_52_low)}` : '—'}</div></div>
          <div className="pstat"><div className="pstat-label">P/E</div><div className="pstat-value">{price.pe_ratio != null ? formatNumber(price.pe_ratio, 1) : '—'}</div></div>
          <div className="pstat"><div className="pstat-label">Fwd P/E</div><div className="pstat-value">{price.forward_pe != null ? formatNumber(price.forward_pe, 1) : '—'}</div></div>
          <div className="pstat"><div className="pstat-label">EPS</div><div className="pstat-value">{price.eps != null ? formatNumber(price.eps, 2) : '—'}</div></div>
          <div className="pstat"><div className="pstat-label">Beta</div><div className="pstat-value">{price.beta != null ? formatNumber(price.beta, 2) : '—'}</div></div>
          <div className="pstat"><div className="pstat-label">Div Yield</div><div className="pstat-value">{price.dividend_yield != null ? `${(Number(price.dividend_yield) * 100).toFixed(2)}%` : '—'}</div></div>
          <div className="pstat"><div className="pstat-label">P/B Ratio</div><div className="pstat-value">{price.price_to_book != null ? formatNumber(price.price_to_book, 2) : '—'}</div></div>
        </div>
      </div>
    </section>
  );
}
