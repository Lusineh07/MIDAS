# services/recommender_api/app.py
from pathlib import Path
from fastapi import FastAPI, HTTPException
from .inference import Recommender, FeatureIn

app = FastAPI(title="MIDAS Recommender API", version="v1")

# Resolve .../MIDAS(-recommender)/training/model_registry/recommender_v0001.joblib
MODEL_PATH = (
    Path(__file__).resolve().parents[2]
    / "training" / "model_registry" / "recommender_v0001.joblib"
)

rec: Recommender | None = None

@app.on_event("startup")  # OK for now; can move to lifespan later
def _load_model():
    global rec
    if not MODEL_PATH.exists():
        raise RuntimeError(f"Model not found at {MODEL_PATH}")
    rec = Recommender(str(MODEL_PATH))

@app.get("/")
def root():
    return {"ok": True, "see": "/docs"}

@app.get("/healthz")
def healthz():
    return {
        "status": "ok",
        "service": "recommender",
        "version": getattr(rec, "version", "unknown"),
        "model_path": str(MODEL_PATH),
        "model_loaded": rec is not None,
    }

@app.post("/api/recommend")
def recommend(payload: FeatureIn):
    if rec is None:
        raise HTTPException(503, "Model not loaded")
    return rec.predict(payload)
