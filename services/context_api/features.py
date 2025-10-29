from __future__ import annotations
import os
from collections import deque
from datetime import datetime, timezone, timedelta
from typing import Optional, Dict, Any, List

import httpx

from .cache import get_cached, put_cached
from .indicators import atr_normalized, ret_pct, above_sma20
from .providers_finnhub import (
    fetch_headlines, FHError,
    fetch_earnings_date as fetch_earnings_finnhub,
    fetch_quote_finnhub,
)
from .providers_tiingo import fetch_candles_tiingo, fetch_quote_tiingo, TiError
from .providers_yahoo import fetch_headlines_yahoo

_QUOTE_RING: dict[str, deque[tuple[datetime, float]]] = {}
SENT_URL = os.getenv("SENT_URL", "http://127.0.0.1:8016")

def iso_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00","Z")

def _parse_iso_aware(s: str) -> datetime:
    if not s: return datetime.now(timezone.utc)
    s2 = s.replace("Z", "+00:00")
    try: d = datetime.fromisoformat(s2)
    except Exception: return datetime.now(timezone.utc)
    if d.tzinfo is None: d = d.replace(tzinfo=timezone.utc)
    return d.astimezone(timezone.utc)

def _note_quote(ticker: str, last: float) -> None:
    ring = _QUOTE_RING.setdefault(ticker, deque(maxlen=600))
    ring.append((datetime.now(timezone.utc), float(last)))
    cut = datetime.now(timezone.utc) - timedelta(minutes=10)
    while ring and ring[0][0] < cut:
        ring.popleft()

def _ret_from_ring(ticker: str, minutes: int) -> float:
    ring = _QUOTE_RING.get(ticker)
    if not ring: return 0.0
    cutoff = datetime.now(timezone.utc) - timedelta(minutes=minutes)
    base = None
    for ts, px in reversed(ring):
        base = px
        if ts <= cutoff: break
    if base is None or base == 0.0: return 0.0
    last = ring[-1][1]
    return (last - base) / base if base else 0.0

def _synthetic_feats() -> dict:
    closes = [100,101,102,103,103,104,105,104,103,102,103,104,103,102,101,100,99,99,100,101,102]
    highs  = [101,102,103,104,104,105,106,105,104,103,104,105,104,103,102,101,100,100,101,102,103]
    lows   = [ 99,100,101,102,102,103,104,103,102,101,102,103,102,101,100, 99, 98, 98, 99,100,101]
    rv20 = atr_normalized(highs, lows, closes, 20)
    r_1m = ret_pct(closes, 1); r_5m = ret_pct(closes, 5)
    return {
        "sent_mean": 0.0, "sent_std": 0.05,
        "r_1m": float(r_1m), "r_5m": float(r_5m),
        "above_sma20": bool(above_sma20(closes)),
        "mins_since_news": 12,
        "rv20": float(min(max(rv20, 0.02), 0.80)),
        "earnings_soon": False,
        "liquidity_flag": True,
    }

def build_features_stub() -> dict:
    return _synthetic_feats()

def _sent_from_headlines(headlines: List[dict]) -> tuple[float, float]:
    titles = [h.get("title","").strip() for h in (headlines or []) if h.get("title")]
    titles = [t for t in titles if t]
    if not titles: return 0.0, 0.05
    try:
        with httpx.Client(timeout=6.0, trust_env=False) as cli:
            r = cli.post(f"{SENT_URL}/api/sentiment", json={"texts": titles[:8]})
            r.raise_for_status()
            d = r.json()
            return float(d.get("mean", 0.0)), float(d.get("std", 0.05))
    except Exception:
        return 0.0, 0.05

def build_features_for(ticker: str) -> Dict[str, Any]:
    live = os.getenv("LIVE_PROVIDERS") == "1"
    error: Optional[str] = None
    top_headline: Optional[dict] = None

    # TTL cache (live only)
    if live:
        cached = get_cached(ticker)
        if cached:
            return cached

    if not live:
        feats = _synthetic_feats()
        payload = {
            "features": feats,
            "top_headline": top_headline,
            "error": error,
            "quote": {"last": 0.0, "bid": None, "ask": None, "quality": "unknown"},
            "ts": iso_now(),
        }
        return payload

    try:
        # ----- Headlines: Finnhub -> Yahoo fallback
        headlines: List[dict] = []
        try:
            headlines = fetch_headlines(ticker, limit=5)
        except FHError as e:
            error = f"news: {e}"
        if not headlines:
            try:
                headlines = fetch_headlines_yahoo(ticker, limit=5)
            except Exception as e:
                error = (error + f"; yahoo: {e}") if error else f"yahoo: {e}"
        if headlines:
            top_headline = headlines[0]

        # ----- Sentiment
        sent_mean, sent_std = _sent_from_headlines(headlines)

        # ----- Quotes + Candles (Tiingo primary)
        quote_ti = fetch_quote_tiingo(ticker)
        candles  = fetch_candles_tiingo(ticker, lookback_minutes=120, freq="1min")

        last_px = float(quote_ti.get("last") or 0.0)
        if last_px == 0.0 and candles:
            last_px = float(candles[-1]["close"])

        bid_disp = float(quote_ti.get("bid") or 0.0) or None
        ask_disp = float(quote_ti.get("ask") or 0.0) or None
        quality = "real" if (bid_disp is not None and ask_disp is not None and last_px > 0) else "unknown"

        # Fallback: Finnhub last if Tiingo last missing
        if last_px <= 0.0:
            try:
                qfh = fetch_quote_finnhub(ticker)
                if qfh.get("last"):
                    last_px = float(qfh["last"])
            except Exception:
                pass

        if last_px <= 0.0: last_px = 1.0  # guard

        _note_quote(ticker, last_px)

        # If B/A still missing or invalid, estimate tight spread (~8 bps)
        if bid_disp is None or ask_disp is None or (ask_disp is not None and bid_disp is not None and ask_disp <= bid_disp):
            spread_bps_est = 8.0
            half = (spread_bps_est / 1e4) * last_px * 0.5
            bid_disp = float(last_px - half)
            ask_disp = float(last_px + half)
            quality = "estimated"

        # ----- mins since news (cap 240)
        mins_since_news = 9999
        if headlines:
            latest = max(_parse_iso_aware(h.get("ts","")) for h in headlines if h.get("ts"))
            mins_since_news = int((datetime.now(timezone.utc) - latest).total_seconds() // 60)
        mins_since_news = min(int(mins_since_news), 240)

        # ----- Returns & rv20 with padding
        if candles and len(candles) >= 2:
            closes = [c["close"] for c in candles]
            highs  = [c["high"]  for c in candles]
            lows   = [c["low"]   for c in candles]
            r_1m = ret_pct(closes, 1) if len(closes) >= 2 else _ret_from_ring(ticker, 1)
            r_5m = ret_pct(closes, 5) if len(closes) >= 6 else _ret_from_ring(ticker, 5)
            def _pad(series: list[float], n: int, pad_val: float) -> list[float]:
                return series + [pad_val] * max(0, n - len(series))
            series = closes[-120:] if closes else []
            if len(series) < 21:
                pad_val = series[-1] if series else last_px
                series = _pad(series, 21, pad_val)
            else:
                pad_val = series[-1]
            hseg = (highs or [pad_val])[-len(series):]
            lseg = (lows  or [pad_val])[-len(series):]
            rv20 = atr_normalized(hseg, lseg, series, 20)
            above = bool(series[-1] > sum(series[-20:]) / 20.0)
        else:
            r_1m = _ret_from_ring(ticker, 1)
            r_5m = _ret_from_ring(ticker, 5)
            rv20  = atr_normalized([last_px]*21, [last_px]*21, [last_px]*21, 20)
            above = False

        rv20 = float(min(max(rv20, 0.02), 0.80))

        # ----- Earnings soon (≤14 days)
        earnings_soon = False
        try:
            earn_iso = fetch_earnings_finnhub(ticker)
            if earn_iso:
                ed = _parse_iso_aware(earn_iso).date()
                today = datetime.now(timezone.utc).date()
                earnings_soon = 0 <= (ed - today).days <= 14
        except FHError:
            pass

        # ----- Liquidity (IEX-friendly)
        spread_bps = abs(ask_disp - bid_disp) / last_px * 1e4 if last_px else 9999
        if candles:
            vol_1m = int(candles[-1]["volume"])
            vol_5m = sum(int(c["volume"]) for c in candles[-5:])
        else:
            vol_1m = 0; vol_5m = 0
        liquidity_flag = (spread_bps <= 30.0) or (vol_1m >= 1_000) or (vol_5m >= 5_000)

        feats = {
            "sent_mean": float(sent_mean), "sent_std": float(sent_std),
            "r_1m": float(r_1m), "r_5m": float(r_5m),
            "above_sma20": bool(above),
            "mins_since_news": int(mins_since_news),
            "rv20": float(rv20),
            "earnings_soon": bool(earnings_soon),
            "liquidity_flag": bool(liquidity_flag),
        }

        payload = {
            "features": feats,
            "top_headline": top_headline,
            "error": error,
            "quote": {"last": float(last_px), "bid": float(bid_disp), "ask": float(ask_disp), "quality": quality},
            "ts": iso_now(),
        }

        # store to TTL cache
        put_cached(ticker, payload)
        return payload

    except TiError as e:
        error = f"tiingo: {e}"
    except Exception as e:
        error = f"providers failed: {e!r}"

    payload = {
        "features": _synthetic_feats(),
        "top_headline": top_headline,
        "error": error,
        "quote": {"last": 0.0, "bid": None, "ask": None, "quality": "unknown"},
        "ts": iso_now(),
    }
    put_cached(ticker, payload)
    return payload
