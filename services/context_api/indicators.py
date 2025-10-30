from __future__ import annotations
import numpy as np
from typing import Sequence

def sma(values: Sequence[float], window: int) -> float:
    a = np.asarray(values[-window:], dtype=float)
    if a.size < window:
        raise ValueError("not enough data for SMA")
    return float(a.mean())

def true_range(high: float, low: float, prev_close: float) -> float:
    return max(high - low, abs(high - prev_close), abs(low - prev_close))

def atr_normalized(highs: Sequence[float], lows: Sequence[float], closes: Sequence[float], window: int = 20) -> float:
    if len(highs) < window + 1 or len(lows) < window + 1 or len(closes) < window + 1:
        raise ValueError("not enough data for ATR")
    trs = [true_range(h, l, pc) for h, l, pc in zip(highs[-window:], lows[-window:], closes[-window-1:-1])]
    atr = float(np.mean(trs))
    last = float(closes[-1])
    return float(atr / last) if last else 0.0

def ret_pct(closes: Sequence[float], delta: int) -> float:
    if len(closes) <= delta:
        raise ValueError("not enough data for return")
    c0, c1 = float(closes[-delta-1]), float(closes[-1])
    return (c1 - c0) / c0 if c0 else 0.0

def above_sma20(closes: Sequence[float]) -> bool:
    return float(closes[-1]) > sma(closes, 20)
