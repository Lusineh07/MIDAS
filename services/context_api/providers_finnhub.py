from __future__ import annotations
import os, time, re
from datetime import datetime, timedelta, timezone
from typing import List, Optional, Dict, Any
import httpx

FINNHUB_TOKEN = os.getenv("FINNHUB_TOKEN") or os.getenv("FINNHUB_API_KEY") or ""
BASE = "https://finnhub.io/api/v1"

TTL_NEWS  = int(os.getenv("FINNHUB_TTL_S", "90"))
TTL_EARN  = int(os.getenv("FINNHUB_EARN_TTL_S", "3600"))
TTL_QUOTE = 15  # seconds

_cache_news:  dict[tuple[str,int], tuple[float, List[Dict[str,Any]]]] = {}
_cache_earn:  dict[str, tuple[float, Optional[str]]] = {}
_cache_quote: dict[str, tuple[float, Dict[str, float]]] = {}

class FHError(Exception):
    pass

def _now() -> float: return time.time()
def _iso(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).isoformat(timespec="seconds").replace("+00:00","Z")

def _http_get(path: str, params: dict) -> dict | list:
    if not FINNHUB_TOKEN:
        raise FHError("FINNHUB_TOKEN missing")
    url = f"{BASE}{path}"
    p   = dict(params or {}); p["token"] = FINNHUB_TOKEN
    with httpx.Client(timeout=10.0, trust_env=False) as cli:
        r = cli.get(url, params=p)
        r.raise_for_status()
        return r.json()

def _aliases_for(t: str) -> list[str]:
    t = t.upper()
    table = {
        "NVDA": ["NVIDIA", "Nvidia"],
        "AMD":  ["Advanced Micro Devices", "AMD"],
        "AAPL": ["Apple"],
        "MSFT": ["Microsoft"],
        "TSLA": ["Tesla"],
        "BAC":  ["Bank of America"],
        "QQQ":  ["Invesco QQQ", "Nasdaq-100", "Nasdaq 100"],
        "MSTR": ["MicroStrategy"],
        "TSMC": ["TSMC", "Taiwan Semiconductor", "Taiwan Semi"],
        "META": ["Meta", "Facebook"],
        "GOOGL":["Alphabet", "Google"],
    }
    return list(dict.fromkeys([t] + table.get(t, [])))

def _score_headline(title: str, ticker: str) -> int:
    if not title: return -999
    score = 0
    aliases = _aliases_for(ticker)
    for i, key in enumerate(aliases, start=1):
        if re.search(rf"\b{re.escape(key)}\b", title, flags=re.IGNORECASE):
            score += 15 * (len(aliases) - i + 1)
        elif re.search(re.escape(key), title, flags=re.IGNORECASE):
            score += 4
    if any(ch in title for ch in (":", "—", "-")): score += 1
    return score

def fetch_headlines(ticker: str, limit: int = 3) -> List[Dict[str, str]]:
    """Return top N headlines relevant to ticker. [{title,publisher,ts,url}]"""
    t = ticker.upper().strip()
    if not t: return []
    ck = (t, max(1, int(limit)))
    hit = _cache_news.get(ck)
    if hit and _now() - hit[0] < TTL_NEWS:
        return hit[1][:ck[1]]

    today = datetime.now(timezone.utc).date()
    frm   = today - timedelta(days=7)
    raw = _http_get("/company-news", {"symbol": t, "from": frm.isoformat(), "to": today.isoformat()})
    items: List[Dict[str,str]] = []
    if isinstance(raw, list):
        for n in raw:
            try:
                title = str(n.get("headline","")).strip()
                if not title: continue
                ts = datetime.fromtimestamp(n.get("datetime",0), tz=timezone.utc)
                items.append({
                    "title": title,
                    "publisher": str(n.get("source","")).strip(),
                    "ts": _iso(ts),
                    "url": str(n.get("url","")).strip(),
                })
            except Exception:
                continue
    items.sort(key=lambda x: (_score_headline(x["title"], t), x.get("ts","")), reverse=True)
    top = [h for h in items if h.get("title") and h.get("url")][:ck[1]]
    _cache_news[ck] = (_now(), top)
    return top

def fetch_earnings_date(ticker: str) -> Optional[str]:
    t = ticker.upper().strip()
    if not t: return None
    hit = _cache_earn.get(t)
    if hit and _now() - hit[0] < TTL_EARN:
        return hit[1]
    try:
        data = _http_get("/calendar/earnings", {"symbol": t})
        cal  = data.get("earningsCalendar") if isinstance(data, dict) else None
        best = None
        if isinstance(cal, list):
            for row in cal:
                ds = str(row.get("date","")).strip()
                if ds:
                    best = f"{ds}T12:00:00Z"
                    break
        _cache_earn[t] = (_now(), best)
        return best
    except Exception:
        _cache_earn[t] = (_now(), None)
        return None

def fetch_quote_finnhub(ticker: str) -> Dict[str, float]:
    """Return {'last': float, 'bid': None, 'ask': None} with short TTL."""
    t = ticker.upper().strip()
    hit = _cache_quote.get(t)
    if hit and _now() - hit[0] < TTL_QUOTE:
        return hit[1]
    data = _http_get("/quote", {"symbol": t})
    last = float(data.get("c") or 0.0)
    out  = {"last": last, "bid": None, "ask": None}
    _cache_quote[t] = (_now(), out)
    return out
