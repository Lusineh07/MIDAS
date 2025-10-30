# MIDAS — Market Insight & Decision Assist System

Windows HUD that, for a ticker, pulls news + quote, computes features, gets a strategy class from a calibrated tree, and renders a ≤180-char one-liner with a clickable headline.

This repository uses the **canonical** layout only:

MIDAS/
services/
context_api/ # /healthz, /api/features, /api/features/v2, /api/one_liner
recommender_api/ # /healthz, /api/recommend (lazy load)
gateway_api/ # /api/run (ctx→rec→one_liner), trust_env=False
sentiment_api/ # /api/sentiment (placeholder; 90s TTL; FR-3)
frontend/ # Electron HUD (Windows)


> **Do not** use/modify `backend/services` (legacy). Only `services/...` is in scope.

---

## Quickstart

### 0) Prereqs

- **Windows 10/11** (HUD) with **Node.js 18+** and **npm 9+**
- **WSL** (Ubuntu recommended) with **Python 3.11+**
- Tokens (if using live providers): create a `.env` file (see `.env.example`)
  - `TIINGO_TOKEN`, `FINNHUB_TOKEN`

### 1) Install Python deps (WSL)

```bash
cd MIDAS
python -m venv .venv
source .venv/bin/activate
pip install -U pip
pip install -r requirements.txt

2) Run the services (WSL)

Open four WSL terminals (or background them). Fixed ports:

Context 8012

Recommender 8014

Gateway 8015

Sentiment 8016

A. Sentiment (FR-3 placeholder)

uvicorn services.sentiment_api.app:app --port 8016

B. Context

Live data (requires tokens):

export LIVE_PROVIDERS=1
export TIINGO_TOKEN=YOUR_TIINGO
export FINNHUB_TOKEN=YOUR_FINNHUB
uvicorn services.context_api.app:app --port 8012

Mocked CI/dev mode (no tokens):

export LIVE_PROVIDERS=0
uvicorn services.context_api.app:app --port 8012

C. Recommender

uvicorn services.recommender_api.app:app --port 8014

D. Gateway

export CTX_URL=http://127.0.0.1:8012
export REC_URL=http://127.0.0.1:8014
uvicorn services.gateway_api.app:app --port 8015

Smoke:

curl -s 'http://127.0.0.1:8012/healthz'
curl -s 'http://127.0.0.1:8014/healthz'
curl -s 'http://127.0.0.1:8015/api/run?ticker=NVDA' | jq '{quote:.quote,rec:.recommendation,age:.cache_age_seconds}'

Notes

All httpx clients use trust_env=False.

Context has a per-ticker TTL cache (default 45 s) and returns a stable ts.

Quote fallback may set quote.quality="estimated" when bid/ask is derived.

3) Start the HUD (Windows Powershell ADMIN)

cd MIDAS\frontend
npm install
npm run start

Usage:

Type a ticker, press Enter (single fetch; no auto-polling).

One-liner = strategy sentence + “Source: Publisher — ” + HEADLINE (clickable).

Only the headline is width-aware and truncates at a word boundary with “…”.

Environment

Ports: 8012 Context, 8014 Recommender, 8015 Gateway, 8016 Sentiment

Tokens: TIINGO_TOKEN, FINNHUB_TOKEN

LIVE_PROVIDERS=0 to run Context in mocked mode (no tokens, useful for CI)

Environment

Ports: 8012 Context, 8014 Recommender, 8015 Gateway, 8016 Sentiment

Tokens: TIINGO_TOKEN, FINNHUB_TOKEN

LIVE_PROVIDERS=0 to run Context in mocked mode (no tokens, useful for CI)

Troubleshooting

HUD shows empty or “NO_ACTION” every time

Verify Gateway is pointing to the right Context/Recommender URLs.

Ensure LIVE_PROVIDERS=1 with valid tokens, or accept mocked features.

Recommender fixed class/prob alignment is in place; if all inputs are degenerate, it can collapse to a default—check features payload from Context.

Headline doesn’t match ticker

Context uses Finnhub first, then Yahoo RSS fallback with alias-aware scoring. Verify the features.headlines source list; if RSS fallback is active, alias mapping may dominate on thin tickers.

Quote status shows quality:"estimated"

Bid/ask missing from provider; we estimate a tight spread. This is expected during off-hours or degraded feeds.

Port conflicts

Something is already listening on 8012/8014/8015/8016. Stop previous instances or change ports locally (keep the canonical map for commits).

Corporate proxy

Clients run with trust_env=False. If you must use a proxy, set direct service URLs on localhost and avoid proxying the loopback.

CI Smoke (optional)

A minimal GitHub Actions workflow is included at /.github/workflows/smoke.yml:

Runs services/recommender_api/tests/test_latency.py

Boots Context in LIVE_PROVIDERS=0 mode and curls /api/features/v2 to validate schema

The smoke avoids external API calls by using mocked providers.