from __future__ import annotations
import os, time
from typing import Dict, Tuple, Optional

# Simple in-proc cache: ticker -> (epoch_secs, payload_dict)
_CACHE: Dict[str, Tuple[float, dict]] = {}

# Default 45s; override with CONTEXT_TTL_S
TTL_S = float(os.getenv("CONTEXT_TTL_S", "45"))

def get_cached(ticker: str) -> Optional[dict]:
    """Return cached payload if fresh, else None."""
    key = (ticker or "").upper().strip()
    if not key:
        return None
    hit = _CACHE.get(key)
    if not hit:
        return None
    ts_epoch, payload = hit
    if (time.time() - ts_epoch) <= TTL_S:
        # annotate (optional)
        payload.setdefault("_cache", {})["age_s"] = int(time.time() - ts_epoch)
        payload["_cache"]["ttl_s"] = int(TTL_S)
        payload["_cache"]["hit"] = True
        return payload
    # stale
    _CACHE.pop(key, None)
    return None

def put_cached(ticker: str, payload: dict) -> None:
    key = (ticker or "").upper().strip()
    if not key or not isinstance(payload, dict):
        return
    _CACHE[key] = (time.time(), payload)

# --------------------------------------------------------------------
# Simple TTL decorator used by providers_tiingo and others
# --------------------------------------------------------------------
import functools

def ttl_cache(ttl_seconds=60):
    """Basic in-memory time-based cache decorator."""
    def decorator(func):
        cache = {}

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            key = (args, tuple(sorted(kwargs.items())))
            now = time.time()
            if key in cache:
                value, ts = cache[key]
                if now - ts < ttl_seconds:
                    return value
            value = func(*args, **kwargs)
            cache[key] = (value, now)
            return value

        return wrapper
    return decorator
