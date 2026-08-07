const SignalPanel = ({ signal, isLoading, isRefreshing, onRefresh, onGenerateSignal }) => {
  const signalValue = signal?.signal || 'WAITING';
  const confidence = signal?.confidence || 'MEDIUM';
  const signalClass = signalValue === 'BUY' ? 'BUY' : signalValue === 'SELL' ? 'SELL' : signalValue === 'HOLD' ? 'HOLD' : 'IDLE';

  return (
    <section className="signal-card">
      <div className="panel-head">
        <span className="panel-title">AI Signal</span>
        <span className="panel-title">{signal?.generated_at ? new Date(signal.generated_at).toLocaleTimeString() : '—'}</span>
      </div>

      <div className={`signal-arena ${signalClass}`}>
        {isLoading ? (
          <>
            <div className="signal-word IDLE" style={{ fontSize: '22px', letterSpacing: 0 }}>Analyzing…</div>
            <div className="signal-subtext">NVIDIA NIM is evaluating all metrics</div>
          </>
        ) : (
          <>
            <div className={`signal-word ${signalClass}`}>{signalValue}</div>
            {signalValue !== 'WAITING' && (
              <div className={`conf-pill cp-${confidence}`}>{confidence} CONFIDENCE</div>
            )}
            <div className="signal-model">{signal?.model_used || 'NVIDIA NIM'}</div>
          </>
        )}
      </div>

      <div className="rationale">
        {(signal?.rationale || []).map((reason, idx) => (
          <div key={`${reason}-${idx}`} className="rat-item">
            <div className={`rat-dot rd-${signalClass}`} />
            <span>{reason}</span>
          </div>
        ))}
        {!signal?.rationale?.length && !isLoading && (
          <div className="rat-item">
            <div className="rat-dot rd-def" />
            <span>Loading a fresh signal will populate rationale here.</span>
          </div>
        )}
      </div>

      <div className="action-row">
        <button type="button" className="btn btn-refresh" onClick={onRefresh} disabled={isRefreshing || isLoading}>
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" aria-hidden="true">
            <polyline points="23 4 23 10 17 10" />
            <path d="M20.49 15a9 9 0 1 1-2.12-9.36L23 10" />
          </svg>
          {isRefreshing ? 'Refreshing…' : 'Refresh'}
        </button>

        <button type="button" className="btn btn-signal" onClick={onGenerateSignal} disabled={isLoading || isRefreshing}>
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" aria-hidden="true">
            <polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2" />
          </svg>
          Get Signal
        </button>
      </div>
    </section>
  );
};

export default SignalPanel;
