# services/recommender_api/inference.py
from __future__ import annotations

import joblib
import numpy as np
from pydantic import BaseModel, Field
from typing import Any, Sequence


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
    """
    Loads a bundle with:
      - tree: a fitted classifier (e.g., DecisionTreeClassifier)
      - cal:  a fitted probability calibrator (e.g., CalibratedClassifierCV)
      - classes: list[str] mapping integer label -> human class name
      - feature_order: list[str] order of features expected by the model
      - version: str
    """

    def __init__(self, model_path: str):
        bundle = joblib.load(model_path)
        self.tree = bundle["tree"]
        self.cal = bundle["cal"]
        self.classes: Sequence[str] = bundle["classes"]
        self.order: Sequence[str] = bundle["feature_order"]
        self.version: str = bundle["version"]

        # Calibrator classes (for indexing probabilities) — may be ints or strings
        self.cal_classes: Sequence[Any] | None = getattr(self.cal, "classes_", None)

    def to_vec(self, f: FeatureIn) -> np.ndarray:
        # Cast booleans to float via float() to align with training
        vals = []
        for k in self.order:
            v = getattr(f, k)
            if isinstance(v, bool):
                v = float(v)
            vals.append(v)
        return np.array(vals, dtype=float).reshape(1, -1)

    @staticmethod
    def _as_label(value: Any) -> Any:
        """
        Normalize predicted label from the tree so it can be compared with cal.classes_.
        If your tree predicts encoded ints (0..K-1), this returns int(value).
        If it predicts strings, returns the string unchanged.
        """
        # try integer conversion first; if it fails, keep original
        try:
            return int(value)
        except Exception:
            return value

    def _prob_for_label(self, probs: np.ndarray, label: Any) -> float:
        """
        Given proba vector and a label (int or str), find the correct column index
        by matching against self.cal_classes. If that fails, fall back to argmax.
        """
        if self.cal_classes is not None:
            try:
                idx = list(self.cal_classes).index(label)
                return float(probs[idx])
            except ValueError:
                # label not found in calibrator classes — fall back to argmax
                pass
        # safest fallback
        return float(probs[np.argmax(probs)])

    def predict(self, f: FeatureIn) -> dict:
        x = self.to_vec(f)

        # Predicted label from the tree (could be int-encoded or string)
        tree_label_raw = self.tree.predict(x)[0]
        tree_label = self._as_label(tree_label_raw)

        # Probabilities from the calibrator
        probs = self.cal.predict_proba(x)[0]

        # Confidence aligned to the predicted label
        confidence = self._prob_for_label(probs, tree_label)

        # Human-readable class name:
        # - If the tree_label is an integer code, map via self.classes[code].
        # - If it's already a string label, use as-is.
        if isinstance(tree_label, int):
            # guard against out-of-range
            if 0 <= tree_label < len(self.classes):
                class_name = self.classes[tree_label]
            else:
                # fallback: best-prob class
                class_name = self.classes[int(np.argmax(probs))]
        else:
            class_name = str(tree_label)

        return {
            "class": class_name,
            "confidence": float(confidence),
            "version": self.version,
        }
