from __future__ import annotations
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Tuple, Optional
from datetime import datetime, timezone
import time, math, os

# -------- Optional FinBERT (HuggingFace) import --------
USE_TRANSFORMERS = True
pipe = None
try:
    if USE_TRANSFORMERS:
        from transformers import pipeline
        # lazy-load happens on first call
        def get_pipe():
            global pipe
            if pipe is None:
                pipe = pipeline("text-classification", model="ProsusAI/finbert")
            return pipe
    else:
        def get_pipe(): return None
except Exception:
    # transformers not installed or model load failed => fallback
    def get_pipe(): return None

# -------- Lightweight fallback scorer (lexicon-based) --------
POS = {"beat","beats","beating","outperform","surge","surges","record","upgrade","upgrades","bullish","rally","rallies","strength"}
NEG = {"miss","misses","warning","downgrade","downgrades","bearish","plunge","plunges","fall","falls","lawsuit","probe","investigation"}

def lexicon_score(s: str) -> float:
    if not s: return 0.0
    t = s.lower()
    pos = sum(1 for w in POS if w in t)
    neg = sum(1 for w in NEG if w in t)
    raw = pos - neg
    if raw == 0: return 0.0
    return max(-1.0, min(1.0, raw/3.0))  # clamp [-1,1]

# -------- API --------
app = FastAPI(title="MIDAS Sentiment API", version="v1")
TTL = float(os.getenv("SENT_TTL_S", "90"))
_CACHE: Dict[Tuple[str, ...], Tuple[float, dict]] = {}

class SentIn(BaseModel):
    texts: List[str]  # plain strings (titles/summaries)

class SentOut(BaseModel):
    ts: str
    n: int
    mean: float
    std: float
    samples: List[float]
    engine: str  # "finbert" or "lexicon"

def _iso_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00","Z")

def _finbert_signed_score(pipe, text: str) -> float:
    """+score for positive, -score for negative, 0 for neutral (FinBERT labels)."""
    try:
        out = pipe(text, truncation=True)[0]
        label = (out["label"] or "").lower()
        score = float(out["score"])
        if "pos" in label:   return +score
        if "neg" in label:   return -score
        return 0.0
    except Exception:
        return lexicon_score(text)

@app.get("/healthz")
def healthz():
    engine = "finbert" if get_pipe() is not None else "lexicon"
    return {"status": "ok", "service": "sentiment", "version": "v1", "ttl_s": TTL, "engine": engine}

@app.post("/api/sentiment", response_model=SentOut)
def analyze(x: SentIn):
    if not x.texts or not isinstance(x.texts, list):
        raise HTTPException(400, "texts required")
    # Normalize input texts
    key = tuple(t.strip() for t in x.texts if isinstance(t, str) and t.strip())
    if not key:
        raise HTTPException(400, "texts required")

    now = time.time()
    hit = _CACHE.get(key)
    if hit and (now - hit[0]) < TTL:
        return hit[1]

    pipe_inst = get_pipe()
    samples: List[float] = []
    if pipe_inst is not None:
        engine = "finbert"
        for t in key:
            samples.append(_finbert_signed_score(pipe_inst, t))
    else:
        engine = "lexicon"
        for t in key:
            samples.append(lexicon_score(t))

    n = len(samples)
    mean = sum(samples)/n if n else 0.0
    var  = sum((v-mean)**2 for v in samples)/n if n else 0.0
    std  = math.sqrt(var)

    out = SentOut(ts=_iso_now(), n=n, mean=float(mean), std=float(std), samples=[float(v) for v in samples], engine=engine).dict()
    _CACHE[key] = (now, out)
    return out