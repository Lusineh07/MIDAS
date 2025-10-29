from __future__ import annotations
import re
import time
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Any, Optional

# Optional: use team's Yahoo helper if available
try:
    # adjust import if your path differs
    from backend.fetch_articles import fetch_articles as fetch_articles_team
except Exception:  # pragma: no cover
    fetch_articles_team = None  # we'll use our internal fetcher

# Internal RSS fallback (only used if team helper import fails)
def _fetch_yahoo_rss(ticker: str, keyword: str) -> List[Dict[str, str]]:
    try:
        import requests, feedparser  # lightweight, commonly available
        rss_url = f"https://finance.yahoo.com/rss/headline?s={ticker}"
        resp = requests.get(rss_url, headers={"User-Agent": "Mozilla/5.0"}, timeout=10)
        resp.raise_for_status()
        feed = feedparser.parse(resp.content)
        k = (keyword or "").lower().strip()
        out = []
        for e in getattr(feed, "entries", []):
            title = (e.get("title") or "").strip()
            summary = (e.get("summary") or "").strip()
            if not title:
                continue
            if k and (k not in title.lower()) and (k not in summary.lower()):
                continue
            link = (e.get("link") or "").strip()
            published = (e.get("published") or "").strip()
            out.append({"title": title, "publisher": "Yahoo", "url": link, "ts": published})
        return out
    except Exception:
        return []

# -------- aliasing & scoring --------

def _aliases_for(t: str) -> List[str]:
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
        "NFLX": ["Netflix"],
        "AMZN": ["Amazon"],
    }
    base = table.get(t, [])
    return list(dict.fromkeys([t] + base))

def _score_title(title: str, ticker: str) -> int:
    if not title:
        return -10_000
    score = 0
    for i, key in enumerate(_aliases_for(ticker), start=1):
        if re.search(rf"\b{re.escape(key)}\b", title, flags=re.IGNORECASE):
            score += 15 * (50 - i)  # earlier alias slightly higher
        elif re.search(re.escape(key), title, flags=re.IGNORECASE):
            score += 4
    # light bias toward headline-y punctuation
    if ":" in title or "—" in title or "-" in title:
        score += 1
    return score

def _iso_from_any(ts: str) -> str:
    """Try to normalize 'published' strings to ISO; fall back to now."""
    if not ts:
        return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00","Z")
    try:
        from dateutil import parser  # available in many envs; safe to try
        dt = parser.parse(ts)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc).isoformat(timespec="seconds").replace("+00:00","Z")
    except Exception:
        return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00","Z")

# -------- public API: merge + rank --------

def merge_rank_headlines(
    ticker: str,
    finnhub_items: List[Dict[str, Any]],
    limit: int = 5,
) -> List[Dict[str, str]]:
    """
    Combine Finnhub + Yahoo-RSS (filtered by aliases), score by relevance, return top N.
    Input Finnhub items format: {title,publisher,ts,url}.
    Output same normalized format.
    """
    t = ticker.upper().strip()
    if not t:
        return []

    # Normalize Finnhub first
    fin_norm: List[Dict[str, str]] = []
    for h in finnhub_items or []:
        title = (h.get("title") or "").strip()
        url   = (h.get("url") or "").strip()
        if not title or not url:
            continue
        ts    = (h.get("ts") or "").strip()
        pub   = (h.get("publisher") or "").strip() or "News"
        fin_norm.append({"title": title, "publisher": pub, "ts": ts, "url": url})

    # Yahoo RSS candidates via team helper first, else fallback
    ya_list: List[Dict[str, str]] = []
    aliases = _aliases_for(t)
    # Try top few aliases (ticker itself first)
    for kw in aliases[:3]:
        if fetch_articles_team:
            try:
                arts = fetch_articles_team(t, kw) or []
                for a in arts:
                    title = (a.get("title") or "").strip()
                    link  = (a.get("link")  or "").strip()
                    ts    = _iso_from_any((a.get("published") or "").strip())
                    if title and link:
                        ya_list.append({"title": title, "publisher": "Yahoo", "ts": ts, "url": link})
            except Exception:
                pass
        else:
            ya_list.extend(_fetch_yahoo_rss(t, kw))

    # Merge, score, and sort
    pool = fin_norm + ya_list
    # Unique by (title,url) to avoid duplicates
    seen = set()
    uniq: List[Dict[str, str]] = []
    for p in pool:
        k = (p["title"], p["url"])
        if k in seen:
            continue
        seen.add(k)
        uniq.append(p)

    uniq.sort(key=lambda x: (_score_title(x["title"], t), x.get("ts", "")), reverse=True)

    # Final pass: keep only sane URLs/titles
    out = [x for x in uniq if x.get("title") and x.get("url")]
    return out[: max(1, int(limit))]
