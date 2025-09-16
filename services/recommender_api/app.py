from fastapi import FastAPI
from pydantic import BaseModel, Field

app = FastAPI(title="MIDAS Recommender API", version="v1")

class FeatureIn(BaseModel):
    sent_mean: float
    sent_std: float
    r_1m: float
    r_5m: float
    above_sma20: bool
    mins_since_news: int = Field(ge=0, le=1440)
    rv20: float
    earnings_soon: bool
    liquidity_flag: bool

class RecOut(BaseModel):
    class_: str = Field(alias="class")
    confidence: float
    version: str
    def dict(self, *a, **k):
        return super().dict(by_alias=True, *a, **k)

@app.post("/api/recommend", response_model=RecOut)
def recommend(_: FeatureIn):
    # stub until model bundle lands
    return RecOut(**{"class": "NO_ACTION", "confidence": 0.5, "version": "v0000"})

# services/recommender_api/app.py
@app.get("/healthz")
def healthz():
    return {"status":"ok","service":"recommender","version":"v1"}
