from __future__ import annotations
import time, re
from typing import List, Dict, Tuple
import requests, feedparser

TTL_S = 90.0
_cache: dict[Tuple[str, int], Tuple[float, List[Dict[str, str]]]] = {}

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

def _score(title: str, ticker: str) -> int:
    if not title:
        return -999
    score = 0
    for i, a in enumerate(_aliases_for(ticker), start=1):
        if re.search(rf"\b{re.escape(a)}\b", title, flags=re.IGNORECASE):
            score += 10 * (10 - i)  # earlier alias weighted a bit more
        elif re.search(re.escape(a), title, flags=re.IGNORECASE):
            score += 3
    return score

def fetch_headlines_yahoo(ticker: str, limit: int = 3) -> List[Dict[str, str]]:
    t = (ticker or "").upper().strip()
    if not t:
        return []
    ck = (t, int(limit or 3))
    now = time.time()
    hit = _cache.get(ck)
    if hit and now - hit[0] < TTL_S:
        return hit[1][:ck[1]]

    url = f"https://finance.yahoo.com/rss/headline?s={t}"
    resp = requests.get(url, headers={"User-Agent":"Mozilla/5.0"}, timeout=10)
    resp.raise_for_status()
    feed = feedparser.parse(resp.content)

    items: List[Dict[str, str]] = []
    for e in getattr(feed, "entries", []):
        title = (e.get("title") or "").strip()
        link  = (e.get("link")  or "").strip()
        ts    = (e.get("published") or "").strip()
        if not title or not link:
            continue
        items.append({"title": title, "publisher": "Yahoo", "ts": ts, "url": link})

    items.sort(key=lambda x: _score(x["title"], t), reverse=True)
    out = items[:ck[1]]
    _cache[ck] = (now, out)
    return out
