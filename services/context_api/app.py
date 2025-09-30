from fastapi import FastAPI
from datetime import datetime, timezone

app = FastAPI(title="MIDAS Context API", version="v1")

def ts_utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")

@app.get("/healthz")
def healthz():
    return {"status": "ok", "service": "context", "version": "v1"}

@app.get("/api/features")
def features(ticker: str):
    # Stub values to unblock FR-4 until FR-2/FR-3 wiring lands
    return {
        "features": {
            "sent_mean": 0.21,
            "sent_std": 0.08,
            "r_1m": 0.003,
            "r_5m": 0.001,
            "above_sma20": True,
            "mins_since_news": 12,
            "rv20": 0.18,
            "earnings_soon": False,
            "liquidity_flag": True,
        },
        "ticker": ticker,
        "ts": ts_utc_now(),
    }

@app.get("/")
def root():
    return {"ok": True, "see": "/docs"}