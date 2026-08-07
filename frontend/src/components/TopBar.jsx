export default function TopBar({ ticker, currentTicker, onTickerChange, onSubmit, onToggleTheme, status, theme }) {
  return (
    <nav className="topbar">
      <div className="logo-wrap">
        <div className="logo-mark" aria-hidden="true">
          <svg viewBox="0 0 26 26" fill="none" xmlns="http://www.w3.org/2000/svg">
            <rect width="26" height="26" rx="6" fill="rgba(0,212,138,0.12)" />
            <polyline points="3,19 8,12 12,15 17,7 23,10" stroke="#00d48a" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" />
            <circle cx="23" cy="10" r="2.2" fill="#00d48a" />
          </svg>
        </div>
        <span>NIM Trader</span>

        <form className="ticker-form" onSubmit={onSubmit}>
          <input
            className="ticker-input"
            value={ticker}
            onChange={(event) => onTickerChange(event.target.value)}
            placeholder="Ticker"
            autoComplete="off"
            spellCheck={false}
            aria-label="Ticker"
          />
          <button type="submit" className="ticker-submit">Load</button>
          <span className="ticker-resolved">{currentTicker}</span>
        </form>
      </div>

      <div className="topbar-right">
        <div className={`live-dot ${status.includes('Fetching') || status.includes('Calling') ? 'loading' : status.includes('Error') ? 'error' : 'active'}`} />
        <span className="status-label">{status}</span>
        <button type="button" className="btn-icon" onClick={onToggleTheme} aria-label="Toggle theme">
          {theme === 'dark' ? (
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79Z" />
            </svg>
          ) : (
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <circle cx="12" cy="12" r="5" />
              <path d="M12 1v2M12 21v2M4.22 4.22l1.42 1.42M18.36 18.36l1.42 1.42M1 12h2M21 12h2M4.22 19.78l1.42-1.42M18.36 5.64l1.42-1.42" />
            </svg>
          )}
        </button>
      </div>
    </nav>
  );
}
