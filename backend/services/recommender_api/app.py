# services/recommender_api/app.py
from fastapi import FastAPI
from pydantic import BaseModel, Field
from .inference import Recommender, FeatureIn

app = FastAPI(title="MIDAS Recommender API", version="v1")
rec = Recommender("training/model_registry/recommender_v0001.joblib")

class RecOut(BaseModel):
    class_: str = Field(alias="class")
    confidence: float
    version: str
    def dict(self, *a, **k): return super().dict(by_alias=True, *a, **k)

@app.get("/healthz")
def healthz(): return {"status":"ok","service":"recommender","version":rec.version}

@app.post("/api/recommend", response_model=RecOut)
def recommend(payload: FeatureIn):
    return RecOut(**rec.predict(payload))
