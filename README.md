# MIDAS — Market Insight & Decision Assist System

Windows HUD that, for a ticker, pulls news and quote data, computes market features, predicts a trading strategy class using a calibrated decision tree, and renders a ≤180-character one-liner with a clickable headline.

---

## 1. Repository Layout

This repository uses the canonical layout only:

```
MIDAS/
 ├── services/
 │    ├── context_api/      # /healthz, /api/features, /api/features/v2, /api/one_liner
 │    ├── recommender_api/  # /healthz, /api/recommend (lazy load)
 │    ├── gateway_api/      # /api/run (ctx → rec → one_liner), trust_env=False
 │    └── sentiment_api/    # /api/sentiment (placeholder; 90s TTL; FR-3)
 └── frontend/              # Electron HUD (Windows)
```

**Do not use or modify** `backend/services` (legacy).  
Only the `services/...` directories are in scope.

---
## 2. System Requirements

- **Operating System:** Windows 10 or 11 (Administrator access required)  
- **Node.js:** v18 or higher  
- **npm:** v9 or higher  
- **WSL:** (Ubuntu recommended) with Python 3.11+   
- **Internet Connection:** Required for live API data
- **Tokens:** TIINGO_TOKEN, FINNHUB_TOKEN (if using live providers)

---
## 3. Environment Configuration

MIDAS uses environment variables to control data sources and tokens.

### Create a `.env` File

Inside the project root (`MIDAS/`), create a file named `.env` with the following contents:

```
# API Tokens (required for live mode)
TIINGO_TOKEN=your_tiingo_token
FINNHUB_TOKEN=your_finnhub_token

# Live mode switch
LIVE_PROVIDERS=1
```
### Explanation

- `LIVE_PROVIDERS=1` enables live data from Tiingo and Finnhub.  
  Use this when you have valid API tokens.
- `LIVE_PROVIDERS=0` enables **mocked mode** (offline or CI).  
  No tokens are required — data is simulated for testing.
- The backend automatically loads `.env` values at startup.  
- Default service ports are:
  - Context API → 8012  
  - Recommender API → 8014  
  - Gateway API → 8015  
  - Sentiment API → 8016  

Example:  
If you are developing without internet access or tokens, set `LIVE_PROVIDERS=0`.  
When deploying or using real data, set `LIVE_PROVIDERS=1`.

---

## 4. Quickstart

### Step 1: Clone the Repository

Open **Windows PowerShell** or **Command Prompt**, then run:

```
cd Documents
git clone https://github.com/Lusineh07/MIDAS.git
cd MIDAS
```

---

### Step 2: Create a Virtual Environment and Install Dependencies

Create and activate a Python virtual environment:

```
python -m venv .venv
source .venv/bin/activate
pip install -U pip
pip install -r requirements.txt
```

---

## 4. Running the Backend

You can run the backend either automatically using the provided script (recommended) or manually for debugging.

### Option A: Quick Start (Recommended)

Run all backend services at once:

```
./run_all.sh
```

This script:
- Activates the virtual environment  
- Installs dependencies if needed  
- Starts all four APIs automatically on fixed ports  

| Service | Port | Description |
|----------|------|-------------|
| Context API | 8012 | Builds features and fetches market data |
| Recommender API | 8014 | Predicts trading strategy from features |
| Gateway API | 8015 | Connects Context and Recommender |
| Sentiment API | 8016 | Handles FinBERT sentiment analysis |

When successful, the terminal will display:

```
MIDAS is running!
Ports:
 - Context API:     http://127.0.0.1:8012
 - Recommender API: http://127.0.0.1:8014
 - Gateway API:     http://127.0.0.1:8015
 - Sentiment API:   http://127.0.0.1:8016
```

Keep this terminal running while MIDAS is active.

---

### Option B: Run Each Service Manually

If needed, you can start each API in a separate terminal window.

**Terminal 1: Context API**
```
export LIVE_PROVIDERS=0
uvicorn services.context_api.app:app --port 8012
```

**Terminal 2: Recommender API**
```
uvicorn services.recommender_api.app:app --port 8014
```

**Terminal 3: Gateway API**
```
export CTX_URL=http://127.0.0.1:8012
export REC_URL=http://127.0.0.1:8014
uvicorn services.gateway_api.app:app --port 8015
```

**Terminal 4: Sentiment API**
```
uvicorn services.sentiment_api.app:app --port 8016
```

---

## 5. Launching the Frontend (HUD Interface)

The frontend runs separately from the backend.

1. Open a new **PowerShell** or **Command Prompt**.  
2. Navigate to the frontend folder:

   ```
   cd MIDAS/frontend
   ```
3. Install dependencies (only once):
   ```
   npm install
   ```
4. Start the Electron HUD:
   ```
   npm run start
   ```

The Electron window should open and display the MIDAS HUD.  
Enter a ticker symbol (e.g., `AAPL`) and press **Enter** to fetch data.

---

## 6. Usage

Type a ticker and press Enter to fetch the current market snapshot.  
MIDAS performs a single fetch (no auto-polling).

The one-liner format:
```
[strategy sentence] — Source: [Publisher] — [Headline...]
```

The headline is clickable and truncates neatly at a word boundary using “…”.

---

## 7. Environment Summary

```
Ports:
  8012  Context API
  8014  Recommender API
  8015  Gateway API
  8016  Sentiment API

Tokens:
  TIINGO_TOKEN
  FINNHUB_TOKEN

LIVE_PROVIDERS=0  # Run Context in mocked mode (no tokens, for CI or offline)
```

---

## 8. Troubleshooting

**HUD shows empty or “NO_ACTION”**  
Verify Gateway URLs and ensure valid tokens are set.  
If using mocked mode (LIVE_PROVIDERS=0), limited data is expected.

**Headline doesn’t match ticker**  
The Context API uses Finnhub first, then Yahoo RSS fallback.  
On low-activity tickers, fallback headlines may appear instead.

**Quote shows quality:"estimated"**  
Occurs during off-hours or when bid/ask data are missing.

**Port conflicts**  
Ensure no other apps are running on ports 8012–8016.

**Corporate proxy**  
HTTP clients use `trust_env=False`. Avoid proxying localhost.

---

## 9. CI Smoke (Optional)

A minimal GitHub Actions workflow is located at:

```
.github/workflows/smoke.yml
```

It:
- Runs `services/recommender_api/tests/test_latency.py`
- Boots Context in `LIVE_PROVIDERS=0` mode
- Validates `/api/features/v2` schema using mocked providers

---

## 10. Sentiment API (Port 8016)

The Sentiment API analyzes text using FinBERT or a fallback lexicon model.

### Endpoint
```
POST /api/sentiment
```

Example request:
```
{
  "texts": ["Good earnings beat", "Weak guidance hurts outlook"]
}
```

Example response:
```
{
  "ts": "...Z",
  "n": 3,
  "mean": 0.12,
  "std": 0.08,
  "samples": [0.2, 0.1, 0.06],
  "engine": "finbert|lexicon"
}
```

To run the service manually:
```
uvicorn services.sentiment_api.app:app --port 8016
```

If FinBERT is unavailable, MIDAS automatically falls back to a lightweight lexicon scorer.  
Each text set is cached for 90 seconds.

---

## 11. Stopping MIDAS

**Backend:**  
- If using `run_all.sh`: Press `Ctrl + C` once in that terminal.  
- If running manually: Press `Ctrl + C` in each terminal window.  

**Frontend:**  
- Close the Electron window, or  
- Press `Ctrl + C` in the frontend terminal.

---

## 12. Notes

- `run_all.sh` is the recommended way to start the system.  
- Keep port mappings consistent with the defaults above.  
- The frontend must run in a separate terminal from the backend.  
- If dependencies are missing, rerun:
  ```
  pip install -r requirements.txt
  ```

---

© MIDAS Project
