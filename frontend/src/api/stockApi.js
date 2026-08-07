const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

async function request(path, options = {}) {
  const response = await fetch(`${API_BASE}${path}`, {
    headers: {
      'Content-Type': 'application/json',
      ...(options.headers || {}),
    },
    ...options,
  });

  if (!response.ok) {
    const payload = await response.json().catch(() => ({}));
    throw new Error(payload.detail || payload.message || response.statusText || 'Request failed');
  }

  return response.json();
}

export const stockApi = {
  getLatestSnapshot: (ticker) => request(`/data/latest?ticker=${encodeURIComponent(ticker)}`),
  refreshSnapshot: (ticker) => request(`/refresh?ticker=${encodeURIComponent(ticker)}`, { method: 'POST' }),
  generateSignal: (ticker) => request(`/signal?ticker=${encodeURIComponent(ticker)}`, { method: 'POST' }),
};

export { API_BASE };
