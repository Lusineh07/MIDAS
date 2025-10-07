# services/recommender_api/inference.py
import joblib, numpy as np
from pydantic import BaseModel, Field

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

class Recommender:
    def __init__(self, model_path: str):
        b = joblib.load(model_path)
        self.tree = b["tree"]
        self.cal = b["cal"]
        self.classes = b["classes"]
        self.order = b["feature_order"]
        self.version = b["version"]

    def to_vec(self, f: FeatureIn):
        return np.array([getattr(f, k) for k in self.order], dtype=float).reshape(1, -1)

    def predict(self, f: FeatureIn):
        x = self.to_vec(f)
        cls_idx = int(self.tree.predict(x)[0]) #class by tree (teacher)
        probs = self.cal.predict_proba(x)[0]
        return {"class": self.classes[cls_idx], "confidence": float(probs[cls_idx]), "version": self.version}
