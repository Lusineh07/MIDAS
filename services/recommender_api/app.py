# services/recommender_api/app.py
from __future__ import annotations
from fastapi import FastAPI, HTTPException
from typing import Dict, Any
import os
import joblib

from .inference import Recommender, FeatureIn

app = FastAPI(title="MIDAS Recommender API", version="v1")

# Default model bundle path (adjust if your repo uses a subfolder)
MODEL_PATH = os.getenv("MODEL_PATH", "services/recommender_api/model.joblib")

@app.get("/healthz")
def healthz():
    return {
        "status": "ok",
        "model_path": MODEL_PATH,
    }

@app.on_event("startup")
def _load_model():
    global model
    if not os.path.exists(MODEL_PATH):
        raise RuntimeError(f"Model bundle not found at {MODEL_PATH}")
    model = Recommender(MODEL_PATH)

@app.post("/api/recommend")
def recommend(features: FeatureIn) -> Dict[str, Any]:
    """Run model inference for the given features."""
    try:
        result = model.predict(features)
        # ensure it has 'class' and 'confidence' keys for Gateway compatibility
        if not isinstance(result, dict) or "class" not in result:
            raise ValueError("Model.predict() did not return expected dict")
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
