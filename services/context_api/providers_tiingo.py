from __future__ import annotations
import os, datetime as dt
from typing import List
import requests
from .providers import Candle, Quote
from .cache import ttl_cache

TIINGO_TOKEN = os.getenv("TIINGO_TOKEN")
IEX_BASE = "https://api.tiingo.com/iex"

class TiError(RuntimeError):
    def __init__(self, msg: str, status: int | None = None):
        super().__init__(msg)
        self.status = status

def _get(url: str, params: dict) -> dict | list:
    if not TIINGO_TOKEN:
        throw = TiError("TIINGO_TOKEN not set", None)
        raise throw
    params = {**params, "token": TIINGO_TOKEN}
    r = requests.get(url, params=params, timeout=8)
    if r.status_code >= 400:
        try:
            detail = r.json()
        except Exception:
            detail = r.text
        raise TiError(f"{r.status_code} error: {detail}", r.status_code)
    try:
        return r.json()
    except Exception as e:
        raise TiError(f"invalid json from Tiingo: {e!r}", r.status_code)

def _f(x, default: float = 0.0) -> float:
    try:
        if x is None or (isinstance(x, str) and x.strip() == ""):
            return default
        return float(x)
    except Exception:
        return default

def _i(x, default: int = 0) -> int:
    try:
        if x is None or (isinstance(x, str) and x.strip() == ""):
            return default
        return int(x)
    except Exception:
        return default

def _parse_iso_aware(s: str) -> dt.datetime:
    if not s:
        return dt.datetime.now(dt.timezone.utc)
    s2 = s.replace("Z", "+00:00")
    try:
        d = dt.datetime.fromisoformat(s2)
    except Exception:
        return dt.datetime.now(dt.timezone.utc)
    if d.tzinfo is None:
        d = d.replace(tzinfo=dt.timezone.utc)
    return d.astimezone(dt.timezone.utc)

@ttl_cache(ttl_seconds=2)
def fetch_quote_tiingo(ticker: str) -> Quote:
    data = _get(f"{IEX_BASE}/{ticker}", {})
    row = data[0] if isinstance(data, list) and data else (data if isinstance(data, dict) else {})
    last = _f(row.get("last", row.get("close", row.get("tngoLast"))), 0.0)
    bid  = _f(row.get("bidPrice", row.get("bid")), 0.0)
    ask  = _f(row.get("askPrice", row.get("ask")), 0.0)

    ts_raw = row.get("timestamp") or row.get("date") or ""
    ts_dt  = _parse_iso_aware(ts_raw)
    ts     = ts_dt.isoformat(timespec="seconds").replace("+00:00", "Z")

    return {"last": last, "bid": bid, "ask": ask, "ts": ts}

@ttl_cache(ttl_seconds=60)
def fetch_candles_tiingo(ticker: str, lookback_minutes: int = 120, freq: str = "1min") -> List[Candle]:
    """
    IEX intraday minute bars:
    GET https://api.tiingo.com/iex/{ticker}/prices?startDate=YYYY-MM-DD&resampleFreq=1min&columns=open,high,low,close,volume,date
    Relaxed strategy: if 'recent' filtering yields too few bars (closed market),
    fall back to the latest N bars regardless of timestamp.
    """
    start_date = (dt.datetime.now(dt.timezone.utc) - dt.timedelta(days=1)).date().isoformat()
    params = {
        "startDate": start_date,
        "resampleFreq": freq,
        "columns": "open,high,low,close,volume,date",
    }
    data = _get(f"{IEX_BASE}/{ticker}/prices", params)
    if not isinstance(data, list) or not data:
        return []

    # First pass: try to keep only last ~lookback_minutes worth by UTC time
    cutoff = dt.datetime.now(dt.timezone.utc) - dt.timedelta(minutes=lookback_minutes + 5)
    filtered: List[Candle] = []
    for row in data:
        ts_raw = row.get("date", "")
        dt_ts = _parse_iso_aware(ts_raw)
        if dt_ts < cutoff:
            continue
        iso = dt_ts.isoformat(timespec="seconds").replace("+00:00", "Z")
        o = _f(row.get("open"), 0.0)
        h = _f(row.get("high"), 0.0)
        l = _f(row.get("low"), 0.0)
        c = _f(row.get("close"), 0.0)
        v = _i(row.get("volume"), 0)
        filtered.append({"ts": iso, "open": o, "high": h, "low": l, "close": c, "volume": v})

    # If we got too few bars (e.g., market closed), fall back to last N bars unfiltered
    if len(filtered) < 6:
        fallback: List[Candle] = []
        for row in data[-max(60, lookback_minutes):]:
            ts_raw = row.get("date", "")
            dt_ts = _parse_iso_aware(ts_raw)
            iso = dt_ts.isoformat(timespec="seconds").replace("+00:00", "Z")
            o = _f(row.get("open"), 0.0)
            h = _f(row.get("high"), 0.0)
            l = _f(row.get("low"), 0.0)
            c = _f(row.get("close"), 0.0)
            v = _i(row.get("volume"), 0)
            fallback.append({"ts": iso, "open": o, "high": h, "low": l, "close": c, "volume": v})
        return fallback

    return filtered
