from __future__ import annotations
from datetime import datetime, timezone
from .indicators import atr_normalized, ret_pct, above_sma20

def iso_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00","Z")

def build_features_stub() -> dict:
    # deterministic stub so we can test wiring immediately
    return {
        "sent_mean": 0.21, "sent_std": 0.08,
        "r_1m": 0.003, "r_5m": 0.001,
        "above_sma20": True,
        "mins_since_news": 12,
        "rv20": 0.18,
        "earnings_soon": False,
        "liquidity_flag": True,
    }

def build_features_for(ticker: str) -> dict:
    # TEMP: use a tiny synthetic series until provider is connected
    closes = [100,101,102,103,103,104,105,104,103,102,103,104,103,102,101,100,99,99,100,101,102]
    highs  = [101,102,103,104,104,105,106,105,104,103,104,105,104,103,102,101,100,100,101,102,103]
    lows   = [ 99,100,101,102,102,103,104,103,102,101,102,103,102,101,100, 99, 98, 98, 99,100,101]
    rv20 = atr_normalized(highs, lows, closes, 20)
    r_1m = ret_pct(closes, 1)
    r_5m = ret_pct(closes, 5)
    return {
        "sent_mean": 0.0, "sent_std": 0.05,
        "r_1m": float(r_1m), "r_5m": float(r_5m),
        "above_sma20": bool(above_sma20(closes)),
        "mins_since_news": 12,
        "rv20": float(min(max(rv20, 0.01), 0.80)),
        "earnings_soon": False,
        "liquidity_flag": True,
    }
