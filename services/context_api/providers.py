from __future__ import annotations
from typing import TypedDict, Optional, List

class Headline(TypedDict):
    title: str
    publisher: str
    ts: str
    url: str

class Candle(TypedDict):
    ts: str
    open: float
    high: float
    low: float
    close: float
    volume: int

class Quote(TypedDict):
    last: float
    bid: float
    ask: float
    ts: str

def fetch_headlines(ticker: str, limit: int = 3) -> List[Headline]: ...
def fetch_candles(ticker: str, interval: str = "1m", lookback: int = 120) -> List[Candle]: ...
def fetch_quote(ticker: str) -> Quote: ...
def fetch_earnings_date(ticker: str) -> Optional[str]: ...
