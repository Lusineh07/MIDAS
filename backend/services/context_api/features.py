from __future__ import annotations
from datetime import datetime, timezone
from .indicators import atr_normalized, ret_pct, above_sma20, sma

def iso_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")

def build_features(
    titles: list[str],
    headlines_ts: list[str], #ISO 8601 strings
    highs: list[float], lows: list[float], closes: list[float], #candles (same bar size)
    last_price: float,
    earnings_date_iso: str | None, #next earning or none
    spread_bps: float | None, volume: int | None,
) -> dict:
    #sentiment placeholders(to be replaced by FR-3 call)
    sent_mean, sent_std = 0.0, 0.0

    mins_since_news = 9999
    if headlines_ts:
        latest = max(datetime.fromisoformat(t.replace("Z", "+00:00")) for t in headlines_ts)
        mins_since_news = int((datetime.now(timezone.utc)-latest).total_seconds()//60)
    
    rv20 = atr_normalized(highs, lows, closes, 20)
    r_1m = ret_pct(closes, 1)
    r_5m = ret_pct(closes, 5)
    above = above_sma20(closes)

    #Earnings soon: within 10 TRading days -> approx. with 14 calendar days for now; replace with trading-day calc later
    earnings_soon = False
    if earnings_date_iso:
        ed = datetime.fromisoformat(earnings_date_iso.replace("Z", "+00:00")).date()
        today = datetime.now(timezone.utc).date()
        delta_days = (ed -today).days
        earnings_soon = (0 <= delta_days <=14) #temporary until trading-days util lands

    #Liquididty: spread + volume thresholds (tunable)
    liquidity_flag = True
    if spread_bps is not None and volume is not None:
        liquidity_flag = (spread_bps <=8) and (volume >= 100_000)

    return {
        "sent_mean": float(sent_mean),
        "sent_std": float(sent_std),
        "r_1m": float(r_1m),
        "r_5m": float(r_5m),
        "above_sma20": bool(above),
        "mins_since_news": int(mins_since_news),
        "rv20": float(min(max(rv20, 0.01), 0.80)),
        "earnings_soon": bool(earnings_soon),
        "liquidity_flag": bool(liquidity_flag),
    }