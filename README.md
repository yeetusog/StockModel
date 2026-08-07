# Stock Model

A stock intelligence application that collects live market data, technical indicators, news sentiment, and AI-generated trading signals for a ticker symbol. The project exposes a FastAPI service, saves snapshots to disk, and can serve a lightweight dashboard for viewing the latest market signal.

## What this application does

This app is designed to answer a simple but useful question:

> For a given stock ticker, what is the current market picture, how do technical indicators look, what is the sentiment of recent headlines, and what signal should I consider?

It combines several layers:

- Live stock price and market metadata retrieval from Yahoo Finance
- Technical analysis using pandas-ta indicators
- News gathering from Yahoo Finance and Google News RSS
- Sentiment scoring with FinBERT
- AI signal generation through NVIDIA NIM / OpenAI-compatible API
- JSON snapshot persistence for history and MCP-friendly reads
- A small dashboard UI served from the frontend folder

---

## Core features

### 1. Real-time stock market data
The app fetches current price, prior close, open/high/low, volume, and related fundamentals for a ticker.

Supported metrics include:

- Current price
- Day range
- Prior close
- Change percentage
- Volume and average volume comparison
- Market cap
- P/E ratio, EPS, beta, dividend yield
- 52-week high/low

This is implemented mainly in the market service layer.

### 2. Technical indicator analysis
The application calculates popular trading indicators such as:

- RSI (14)
- MACD and histogram
- SMA 20 / SMA 50
- EMA 12 / EMA 26
- Bollinger Bands
- Trend classification (bullish / bearish / neutral)
- Volume vs average volume percentage

These values are computed from recent market history and turned into a structured `TechnicalIndicators` model.

### 3. News retrieval and aggregation
The app gathers recent headlines from:

- Yahoo Finance ticker news feed
- Google News RSS search results

Each item is normalized into a `NewsItem` model with fields like:

- source
- title
- url
- publisher
- published date

### 4. FinBERT sentiment analysis
Each article title is passed through a FinBERT sentiment model to score the tone of the story.

The result is converted into:

- sentiment_score
- sentiment_magnitude
- sentiment_label

Then all article-level results are summarized into a `SentimentSummary` with:

- mean score
- positivity/neutrality/negativity counts
- overall label

### 5. AI trading signal generation
The app packages the latest market snapshot and asks NVIDIA NIM to classify the signal as:

- BUY
- SELL
- HOLD

This uses a prompt built from price, technical, sentiment, and headline data. The generated result includes:

- signal
- confidence
- rationale
- model used
- generated timestamp

### 6. Persistent snapshot storage
Each refresh stores a snapshot in the `data/snapshots` folder.

It saves:

- a latest snapshot per ticker
- an archived historical snapshot with a timestamped filename

This allows:

- reading the current state easily
- reviewing historical data later
- connecting the app to external tools or MCP consumers

### 7. Dashboard frontend
The app serves a browser dashboard from the `frontend` directory and exposes it at the root URL when the folder exists.

This gives a lightweight UI showing:

- current ticker price
- change and trend
- indicators
- sentiment
- news headlines
- AI-generated signal

---

## Project structure

```text
StockModel/
├── main.py                      # FastAPI app entry point
├── requirements.txt            # Python dependencies
├── mcp_server.json             # MCP endpoint metadata
├── README.md                   # Project documentation
├── app/
│   ├── config.py               # application settings (.env-driven)
│   ├── models/
│   │   └── snapshot.py         # Pydantic data models
│   ├── routers/
│   │   └── signal.py           # API routes for refresh / signal / data access
│   └── services/
│       ├── llm.py              # NVIDIA NIM / OpenAI signal generation
│       ├── market.py           # Price + technical indicator logic
│       ├── news.py             # Yahoo + Google news fetchers
│       ├── sentiment.py        # FinBERT sentiment scoring
│       ├── storage.py          # Snapshot persistence logic
│       └── ...
├── data/
│   └── snapshots/              # Latest and archived ticker JSON snapshots
├── frontend/
│   ├── package.json            # React + Vite frontend scripts
│   ├── vite.config.js          # Vite config for local dev server
│   ├── index.html              # Root HTML shell for React app
│   ├── src/
│   │   ├── App.jsx             # main dashboard composition
│   │   ├── main.jsx            # React bootstrap
│   │   ├── styles.css          # design system and dashboard styling
│   │   ├── api/
│   │   │   └── stockApi.js     # API client for backend endpoints
│   │   └── components/
│   │       ├── TopBar.jsx
│   │       ├── PricePanel.jsx
│   │       ├── TechnicalPanel.jsx
│   │       ├── SentimentPanel.jsx
│   │       ├── NewsPanel.jsx
│   │       └── SignalPanel.jsx
│   └── dist/                   # optional production build output generated by Vite
├── .env                        # Optional local environment variables
└── .venv/                      # Local Python virtual environment
```

### React frontend architecture

The dashboard has been refactored into a proper React application using Vite:

- `App.jsx` orchestrates the page state and API calls
- `components/` contains presentation-level widgets for the price, sentiment, news, and signal panels
- `api/stockApi.js` centralizes backend integration for `/refresh`, `/signal`, and `/data/latest`
- `styles.css` contains the full design system and layout styling
- `main.jsx` bootstraps the React tree into the HTML shell

This structure keeps the UI maintainable and separates business logic from presentation.

---

## Configuration

The app reads settings from a `.env` file in the project root.

Example backend `.env`:

```env
NVIDIA_API_KEY=your_key_here
NVIDIA_NIM_MODEL=meta/llama-3.3-70b-instruct
NVIDIA_NIM_BASE_URL=https://integrate.api.nvidia.com/v1
TICKER=AAPL
LOG_LEVEL=INFO
```

Optional frontend environment file for React:

```env
VITE_API_BASE_URL=http://localhost:8000
```

Notes:

- `NVIDIA_API_KEY` is required for the `/signal` endpoint to work.
- `TICKER` is the default ticker used when a request does not pass one explicitly.
- `VITE_API_BASE_URL` tells the React app where the FastAPI backend is running.
- If the API key is missing, the LLM signal route returns an error instead of generating a signal.

---

## API endpoints

The app exposes a FastAPI service with routes such as:

### Health check

```bash
GET /health
```

Returns application status and environment readiness.

### Refresh snapshot

```bash
POST /refresh?ticker=AAPL
```

This fetches:

- live price data
- technical indicators
- market news
- sentiment analysis
- persisted snapshot

### Generate AI signal

```bash
POST /signal?ticker=AAPL
```

This loads the most recent snapshot and asks NVIDIA NIM for a final BUY / SELL / HOLD recommendation.

### Latest snapshot data

```bash
GET /data/latest?ticker=AAPL
```

Returns the latest saved snapshot JSON.

### Historical snapshots

```bash
GET /history?ticker=AAPL&limit=20
```

Returns archived snapshot records for that ticker.

---

## How to start the application

Use these commands each time you want to run the app locally.

### Option 1: Run the backend only

From the project root:

```bash
cd "/Users/ayushipushkarna/Desktop/Stock Project/StockModel"
source ../.venv/bin/activate
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

Then open the API or use the frontend on another port if you are running it separately.

### Option 2: Run the backend via Python entry point

```bash
cd "/Users/ayushipushkarna/Desktop/Stock Project/StockModel"
source ../.venv/bin/activate
python main.py
```

This executes the same FastAPI app and starts Uvicorn with reload enabled by default.

### Option 3: Run the React dashboard in development mode

From the frontend folder:

```bash
cd "/Users/ayushipushkarna/Desktop/Stock Project/StockModel/frontend"
npm install
npm run dev
```

Then open:

```text
http://localhost:5173/
```

This runs the React app independently and talks to the backend at `http://localhost:8000` by default.

### Option 4: Build the React app and serve it from FastAPI

If you want the backend to serve the production frontend bundle:

```bash
cd "/Users/ayushipushkarna/Desktop/Stock Project/StockModel/frontend"
npm install
npm run build
```

Then start the FastAPI app again:

```bash
cd "/Users/ayushipushkarna/Desktop/Stock Project/StockModel"
source ../.venv/bin/activate
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

The app will serve the built frontend at:

```text
http://localhost:8000/
```

### Option 5: Run without reloading

```bash
cd "/Users/ayushipushkarna/Desktop/Stock Project/StockModel"
source ../.venv/bin/activate
uvicorn main:app --host 0.0.0.0 --port 8000
```

Use this when you want a stable single run without auto-reload.

---

## First-time setup

If you have not installed the app dependencies yet:

```bash
cd "/Users/ayushipushkarna/Desktop/Stock Project/StockModel"
source ../.venv/bin/activate
python -m pip install -r requirements.txt
```

If the environment is not already created, create one first:

```bash
cd "/Users/ayushipushkarna/Desktop/Stock Project"
python3 -m venv .venv
source .venv/bin/activate
cd StockModel
python -m pip install -r requirements.txt
```

For the React frontend, install JavaScript dependencies separately:

```bash
cd "/Users/ayushipushkarna/Desktop/Stock Project/StockModel/frontend"
npm install
```

> Node.js and npm must be installed for the frontend to run locally.

---

## Typical workflow

1. Activate the Python virtual environment.
2. Start the FastAPI backend:

```bash
cd "/Users/ayushipushkarna/Desktop/Stock Project/StockModel"
source ../.venv/bin/activate
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

3. Refresh market data:

```bash
curl -X POST "http://localhost:8000/refresh?ticker=AAPL"
```

4. Generate a signal:

```bash
curl -X POST "http://localhost:8000/signal?ticker=AAPL"
```

5. Read the latest market snapshot:

```bash
curl "http://localhost:8000/data/latest?ticker=AAPL"
```

6. Open the dashboard in your browser:

- React dev version: `http://localhost:5173/`
- Backend-served build version: `http://localhost:8000/`

---

## Frontend and backend coordination

The frontend React app is designed to consume the FastAPI backend through the `VITE_API_BASE_URL` environment variable.

If you are running the backend locally on port `8000`, the default value is:

```env
VITE_API_BASE_URL=http://localhost:8000
```

This keeps the frontend and backend decoupled while letting them communicate cleanly during local development.

---

## Notes about data and reliability

- The app relies on public market data sources and may occasionally fail if Yahoo Finance or news endpoints rate-limit or change structure.
- It includes fallback logic for chart and history retrieval.
- It logs warnings/errors instead of crashing when a provider fails.
- The AI signal generation depends on a valid NVIDIA API key and a working network connection.

---

## Summary

This project acts as a stock signal engine that blends:

- live market data
- technical analysis
- article sentiment
- AI interpretation

into a coherent trading snapshot.

It is useful for:

- research workflows
- dashboard monitoring
- snapshot-based signal generation
- experimentation with market analysis pipelines

If you want to extend the app, the natural next steps are adding a richer UI, a database backend, or a stronger strategy engine on top of the same snapshot data.
