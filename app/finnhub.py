# app/finnhub.py
# -----------------------------
# Purpose:
#   Handles all communication with the Finnhub API (quotes and news).


import httpx
from datetime import datetime, timedelta, timezone

#Case URL for all Finnhub API endpoints
FINNHUB_BASE = "https://finnhub.io/api/v1"

class FinnhubClient:

    #A lightweight asynchronous client to interact with Finnhub endpoints
    def __init__(self, api_key: str, timeout: float = 10.0):
        self.api_key = api_key
        self._client = httpx.AsyncClient(timeout=timeout)

    async def close(self):
        #Close HTTP connection cleanly
        await self._client.aclose()

    #fetch a stock quotes
    async def get_quote(self, symbol: str):
        #Fetch current stock quote
        url = f"{FINNHUB_BASE}/quote"
        params = {"symbol": symbol, "token": self.api_key}
        #send GET request
        r = await self._client.get(url, params=params)
        #Error if status is not 200
        r.raise_for_status()
        return r.json()

    #Fetch company news form Finnhub
    async def get_company_news(self, symbol: str, days: int = 5):
        #Date range from x days to today
        to_dt = datetime.now(timezone.utc).date()
        from_dt = to_dt - timedelta(days=days)
        url = f"{FINNHUB_BASE}/company-news"
        params = {
            "symbol": symbol,
            "from": from_dt.isoformat(),
            "to": to_dt.isoformat(),
            "token": self.api_key,
        }
        r = await self._client.get(url, params=params)
        r.raise_for_status()
        return r.json()
