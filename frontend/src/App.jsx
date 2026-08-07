import { useEffect, useMemo, useState } from 'react';
import { stockApi } from './api/stockApi';
import TopBar from './components/TopBar';
import PricePanel from './components/PricePanel';
import TechnicalPanel from './components/TechnicalPanel';
import SentimentPanel from './components/SentimentPanel';
import NewsPanel from './components/NewsPanel';
import SignalPanel from './components/SignalPanel';

const DEFAULT_TICKER = 'AAPL';
const INDIAN_TICKERS = /^(BEL|ICICIBANK|RELIANCE|TCS|INFY|HDFCBANK|WIPRO|SBIN|TATAMOTORS|AXISBANK)$/i;

function resolveTicker(rawValue) {
  const input = rawValue.trim().toUpperCase();
  if (!input) return DEFAULT_TICKER;
  if (input.includes('.')) return input;
  if (INDIAN_TICKERS.test(input)) return `${input}.NS`;
  return input;
}

const formatTime = (value) => {
  if (!value) return '—';
  try {
    return new Date(value).toLocaleTimeString();
  } catch {
    return '—';
  }
};

export default function App() {
  const [ticker, setTicker] = useState(DEFAULT_TICKER);
  const [snapshot, setSnapshot] = useState(null);
  const [signal, setSignal] = useState(null);
  const [theme, setTheme] = useState('dark');
  const [status, setStatus] = useState('No data');
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [isGeneratingSignal, setIsGeneratingSignal] = useState(false);
  const [error, setError] = useState('');

  const currentTicker = useMemo(() => resolveTicker(ticker), [ticker]);

  const loadLatestSnapshot = async (nextTicker = currentTicker) => {
    try {
      const data = await stockApi.getLatestSnapshot(nextTicker);
      setSnapshot(data);
      setSignal(data.llm_signal || null);
      setStatus(`Loaded ${formatTime(data.timestamp)}`);
      setError('');
      return data;
    } catch (err) {
      setError(err.message);
      setStatus('Backend offline');
      return null;
    }
  };

  useEffect(() => {
    loadLatestSnapshot(DEFAULT_TICKER);
  }, []);

  const handleTickerSubmit = async (event) => {
    event.preventDefault();
    const nextTicker = resolveTicker(ticker);
    setTicker(nextTicker);
    await loadLatestSnapshot(nextTicker);
  };

  const handleRefresh = async () => {
    const nextTicker = resolveTicker(ticker);
    setIsRefreshing(true);
    setStatus('Fetching…');
    setError('');

    try {
      await stockApi.refreshSnapshot(nextTicker);
      const data = await loadLatestSnapshot(nextTicker);
      if (data) {
        setStatus(`Updated ${formatTime(data.timestamp)}`);
      }
    } catch (err) {
      setError(err.message);
      setStatus('Error');
    } finally {
      setIsRefreshing(false);
    }
  };

  const handleSignal = async () => {
    const nextTicker = resolveTicker(ticker);
    setIsGeneratingSignal(true);
    setStatus('Calling AI…');
    setError('');

    try {
      const result = await stockApi.generateSignal(nextTicker);
      setSignal(result);
      setStatus(`Signal: ${result.signal}`);
    } catch (err) {
      setError(err.message);
      setStatus('Signal failed');
    } finally {
      setIsGeneratingSignal(false);
    }
  };

  const toggleTheme = () => {
    setTheme((prev) => (prev === 'dark' ? 'light' : 'dark'));
  };

  return (
    <div className="app-shell" data-theme={theme}>
      <TopBar
        ticker={ticker}
        currentTicker={currentTicker}
        onTickerChange={setTicker}
        onSubmit={handleTickerSubmit}
        onToggleTheme={toggleTheme}
        status={status}
        theme={theme}
      />

      <main className="main-layout">
        <div className="data-column">
          <PricePanel snapshot={snapshot} />

          <div className="two-column-grid">
            <TechnicalPanel snapshot={snapshot} />
            <SentimentPanel snapshot={snapshot} />
          </div>

          <NewsPanel snapshot={snapshot} />
        </div>

        <div className="signal-column">
          <SignalPanel
            signal={signal}
            isLoading={isGeneratingSignal}
            isRefreshing={isRefreshing}
            onRefresh={handleRefresh}
            onGenerateSignal={handleSignal}
          />
        </div>
      </main>

      {error ? <div className="toast toast-error">{error}</div> : null}
    </div>
  );
}
