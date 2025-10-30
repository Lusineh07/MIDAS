from fastapi import FastAPI, HTTPException
from datetime import datetime, timezone
from pydantic import BaseModel
from .features import build_features_stub, build_features_for
import logging

app = FastAPI(title="MIDAS Context API", version="v1")
log = logging.getLogger("context_api")

def ts_utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")

@app.get("/healthz")
def healthz():
    return {"status": "ok", "service": "context", "version": "v1"}

@app.get("/api/features")
def features_stub(ticker: str):
    if not ticker or not ticker.strip():
        raise HTTPException(status_code=422, detail="ticker is required")
    return {"features": build_features_stub(), "ticker": ticker, "ts": ts_utc_now()}

@app.get("/api/features/v2")
def features_v2(ticker: str):
    if not ticker or not ticker.strip():
        raise HTTPException(status_code=422, detail="ticker is required")
    try:
        bundle = build_features_for(ticker)  # {"features":..., "top_headline":..., "quote":..., "error":...}
        resp = {
            "features": bundle.get("features", {}),
            "ticker": ticker,
            "ts": ts_utc_now(),
        }
        if bundle.get("top_headline"):
            resp["top_headline"] = bundle["top_headline"]
        if bundle.get("quote"):
            resp["quote"] = bundle["quote"]
        if bundle.get("error"):
            resp["error"] = bundle["error"]
        return resp
    except Exception as e:
        log.exception("features_v2 failed for %s", ticker)
        return {
            "features": build_features_stub(),
            "ticker": ticker,
            "ts": ts_utc_now(),
            "error": str(e),
        }

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
    msg = (
        f"{x.class_}: {risk}. Conf {x.confidence:.0%}. "
        f"Source: {x.publisher} — {x.title[:80]} {x.url}"
    )
    return {"text": msg[:180]}
