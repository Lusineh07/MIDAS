from __future__ import annotations
from typing import Optional, Dict, Any
from fastapi import FastAPI, HTTPException, Query
import os, httpx, time
from datetime import datetime, timezone

CTX_URL = os.getenv("CTX_URL", "http://127.0.0.1:8012")
REC_URL = os.getenv("REC_URL", "http://127.0.0.1:8014")

TIMEOUT = float(os.getenv("GATEWAY_TIMEOUT_S", "8"))
RETRIES = int(os.getenv("GATEWAY_RETRIES", "2"))
DELAY   = float(os.getenv("GATEWAY_RETRY_DELAY_S", "0.25"))

app = FastAPI(title="MIDAS Gateway API", version="v1")

def iso_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")

def _parse_iso(s: str) -> Optional[datetime]:
    if not s:
        return None
    try:
        return datetime.fromisoformat(s.replace("Z", "+00:00")).astimezone(timezone.utc)
    except Exception:
        return None

@app.get("/healthz")
def healthz():
    return {
        "status": "ok",
        "service": "gateway",
        "version": "v1",
        "CTX_URL": CTX_URL,
        "REC_URL": REC_URL,
        "ts": iso_now(),
    }

def _get_json(url: str, params: dict | None = None) -> dict:
    last_exc: Optional[Exception] = None
    with httpx.Client(timeout=TIMEOUT, trust_env=False) as client:
        for _ in range(RETRIES + 1):
            try:
                r = client.get(url, params=params)
                r.raise_for_status()
                return r.json()
            except Exception as e:
                last_exc = e
                time.sleep(DELAY)
    raise HTTPException(status_code=502, detail=f"GET {url} failed: {last_exc}")

def _post_json(url: str, payload: dict) -> dict:
    last_exc: Optional[Exception] = None
    with httpx.Client(timeout=TIMEOUT, trust_env=False) as client:
        for _ in range(RETRIES + 1):
            try:
                r = client.post(url, json=payload)
                r.raise_for_status()
                return r.json()
            except Exception as e:
                last_exc = e
                time.sleep(DELAY)
    raise HTTPException(status_code=502, detail=f"POST {url} failed: {last_exc}")

@app.get("/api/run")
def run(t: str = Query(..., alias="ticker")) -> Dict[str, Any]:
    ctx = _get_json(f"{CTX_URL}/api/features/v2", params={"ticker": t})

    features: Dict[str, Any] = ctx.get("features", {}) or {}
    top_headline: Optional[Dict[str, str]] = ctx.get("top_headline")
    feature_note = ctx.get("error")
    quote: Dict[str, float | None] = ctx.get("quote") or {"last": 0.0, "bid": None, "ask": None}
    ts_ctx = ctx.get("ts")  # context timestamp if provided

    rec = _post_json(f"{REC_URL}/api/recommend", features)

    headline = top_headline or {"title": "", "publisher": "", "url": ""}
    try:
        one = _post_json(f"{CTX_URL}/api/one_liner", {
            "class_":     rec.get("class", "NO_ACTION"),
            "confidence": rec.get("confidence", 0.0),
            "title":      headline.get("title", ""),
            "publisher":  headline.get("publisher", ""),
            "url":        headline.get("url", ""),
        })
    except HTTPException:
        one = {"text": f"{rec.get('class','NO_ACTION')} · {int(rec.get('confidence',0)*100)}% confidence"}

    # cache age
    now = datetime.now(timezone.utc)
    t_ctx = _parse_iso(ts_ctx) if isinstance(ts_ctx, str) else None
    age_s = int((now - t_ctx).total_seconds()) if t_ctx else None

    resp = {
        "ticker": t,
        "features": features,
        "features_used": features,  # debug
        "recommendation": rec,
        "one_liner": one,
        "quote": quote,             # always present; bid/ask may be null
        "ts_ctx": ts_ctx,
        "ts_gateway": iso_now(),
        "cache_age_seconds": age_s,
    }
    if feature_note:
        resp["features_note"] = feature_note
    if top_headline:
        resp["top_headline"] = top_headline
    return resp
