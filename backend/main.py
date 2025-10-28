# app/main.py
# -----------------------------
# Purpose:
#   The entry point for the FastAPI app.
#   Provides endpoints: /health, /quote, /news
#   Uses caching and async requests to manage API calls efficiently.


#FastAPI Imports for web API
from fastapi import FastAPI, HTTPException, Query
#Allows API be called from web app on another port
from fastapi.middleware.cors import CORSMiddleware
#TTLCache help cahe APO responses
from cachetools import TTLCache
from datetime import datetime, timezone
from typing import Dict
import asyncio

#Local modules
from .config import settings
from .models import Quote, Headline, NewsResponse
from .finnhub import FinnhubClient

#Web server
app = FastAPI(title="MIDAS Quotes & News", version="0.1.0")

#Web forntends talk to API without Browser CORS blocking Time.
if settings.origins:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

#Small caches for quotes and news 
quotes_cache = TTLCache(maxsize=256, ttl=30)   # Cache quotes 30s
news_cache = TTLCache(maxsize=256, ttl=600)    # Cache news 10 mins
_locks: Dict[str, asyncio.Lock] = {}

#helper to get a locker per symbol so request dont race.
def _lock_for(key: str) -> asyncio.Lock:
    if key not in _locks:
        _locks[key] = asyncio.Lock()
    return _locks[key]

#Validate and clean ticker symbols 
def _clean_symbol(symbol: str) -> str:
    s = symbol.strip().upper()
    if not s:
        raise HTTPException(status_code=400, detail="Symbol required")
    return s
# #test enpoint
# @app.get("/health")
# async def health():
#     return {"ok": True, "ts": datetime.now(timezone.utc).isoformat()}

# -------------------------------------------------------------------------
# /quote endpoint: get latest stock quote
# -------------------------------------------------------------------------

@app.get("/quote", response_model=Quote)
async def quote(symbol: str = Query(..., description="Ticker e.g. AAPL")):
    symbol = _clean_symbol(symbol)
    
    #Verify API exist from .env
    if not settings.FINNHUB_API_KEY or settings.FINNHUB_API_KEY.lower() == "your_key_here":
        raise HTTPException(status_code=503, detail="FINNHUB_API_KEY not configured")

    #Use cache if available
    if symbol in quotes_cache:
        return quotes_cache[symbol]

    #One Finnhub call per symbol at a time
    lock = _lock_for(f"q:{symbol}")
    async with lock:
        #double check inside the lock to avoid duplicates
        if symbol in quotes_cache:
            return quotes_cache[symbol]

        #Create a finngub client
        client = FinnhubClient(settings.FINNHUB_API_KEY)
        try:
            #latets quote for symbol
            data = await client.get_quote(symbol)
        finally:
            await client.close()

        #FIeld names into readable one 
        q = Quote(
            symbol=symbol,
            last=float(data.get("c") or 0.0), #current price
            open=float(data.get("o") or 0.0), #opening price
            prev_close=float(data.get("pc") or 0.0), #previous close
            high=float(data.get("h") or 0.0), # high of the day
            low=float(data.get("l") or 0.0),#low of the day
            ts=int(data.get("t") or 0), # timestamp(Epock seconds)
        )
        #save to cache and return
        quotes_cache[symbol] = q
        return q

# -------------------------------------------------------------------------
# /news endpoint: get latest headlines for a stock
# -------------------------------------------------------------------------

@app.get("/news", response_model=NewsResponse)
async def news(symbol: str, limit: int = Query(3, ge=1, le=10)):
    symbol = _clean_symbol(symbol)

    #verify API
    if not settings.FINNHUB_API_KEY or settings.FINNHUB_API_KEY.lower() == "your_key_here":
        raise HTTPException(status_code=503, detail="FINNHUB_API_KEY not configured")

    if symbol in news_cache:
        return NewsResponse(symbol=symbol, items=news_cache[symbol][:limit])

    lock = _lock_for(f"n:{symbol}")
    async with lock:
        if symbol in news_cache:
            return NewsResponse(symbol=symbol, items=news_cache[symbol][:limit])

        client = FinnhubClient(settings.FINNHUB_API_KEY)
        try:
            data = await client.get_company_news(symbol, days=5)
        finally:
            await client.close()
        
        #Convert FInnhub new items into structured headlines.
        items = []
        for it in data:
            try:
                ts = it.get("datetime") or it.get("time") or it.get("publishedTime")
                dt = (datetime.fromtimestamp(int(ts), tz=timezone.utc)
                      if isinstance(ts, (int, float, str)) and str(ts).isdigit()
                      else datetime.fromisoformat(str(ts).replace("Z", "+00:00")))
            except Exception:
                dt = datetime.now(timezone.utc)
                
            #Build headline object
            items.append(Headline(
                symbol=symbol,
                source=str(it.get("source") or it.get("site") or "unknown"),
                headline=str(it.get("headline") or it.get("title") or ""),
                url=str(it.get("url") or ""),
                datetime=dt,
            ))
        #Sort newest to oldest
        items.sort(key=lambda x: x.datetime, reverse=True)
        #Cache and return only request limit
        news_cache[symbol] = items
        return NewsResponse(symbol=symbol, items=items[:limit])