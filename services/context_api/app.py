from fastapi import FastAPI
from datetime import datetime, timezone
from pydantic import BaseModel
from .features import build_features_stub, build_features_for

app = FastAPI(title="MIDAS Context API", version="v1")

def ts_utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00","Z")

@app.get("/healthz")
def healthz():
    return {"status":"ok","service":"context","version":"v1"}

@app.get("/api/features")
def features_stub(ticker: str):
    return {"features": build_features_stub(), "ticker": ticker, "ts": ts_utc_now()}

@app.get("/api/features/v2")
def features_v2(ticker: str):
    feats = build_features_for(ticker)
    return {"features": feats, "ticker": ticker, "ts": ts_utc_now()}

class OneLinerIn(BaseModel):
    class_: str
    confidence: float
    title: str = ""
    publisher: str = ""
    url: str = ""

@app.post("/api/one_liner")
def one_liner(x: OneLinerIn):
    risk = {
        "IRON_CONDOR": "range-bound, IV watch",
        "DEBIT_CALL": "bullish, defined risk",
        "DEBIT_PUT": "bearish, defined risk",
        "COVERED_CALL": "income, upside capped",
        "NO_ACTION": "signal unclear",
    }.get(x.class_, "review setup")
    msg = f"{x.class_}: {risk}. Conf {x.confidence:.0%}. Source: {x.publisher} — {x.title[:80]} {x.url}"
    return {"text": msg[:180]}
