# training/train_tree.py
from pathlib import Path
import json, os
import numpy as np, pandas as pd, joblib
from sklearn.tree import DecisionTreeClassifier
from sklearn.calibration import CalibratedClassifierCV
from sklearn.metrics import accuracy_score, brier_score_loss

VERSION = "v0001"
MAX_DEPTH = int(os.environ.get("MAX_DEPTH", 7))
CV_FOLDS  = int(os.environ.get("CALIB_CV", 3))

FEATURE_ORDER = [
    "sent_mean","sent_std","r_1m","r_5m",
    "above_sma20","mins_since_news","rv20",
    "earnings_soon","liquidity_flag"
]
CLASSES = ["NO_ACTION","IRON_CONDOR","DEBIT_CALL","DEBIT_PUT","COVERED_CALL"]

DATA = Path("training/data")
REG  = Path("training/model_registry"); REG.mkdir(parents=True, exist_ok=True)

def load(split):
    df = pd.read_parquet(DATA / f"synthetic_{split}.parquet")
    X = df[FEATURE_ORDER].astype(float).to_numpy()
    y = df["label"].map({c:i for i,c in enumerate(CLASSES)}).to_numpy()
    return X, y

Xtr, ytr = load("train")
Xva, yva = load("val")
Xte, yte = load("test")

# 1) Primary tree (used for class decisions)
tree = DecisionTreeClassifier(
    max_depth=MAX_DEPTH,
    criterion="entropy",      # often fits rule boundaries better
    random_state=7
)
tree.fit(Xtr, ytr)

# 2) Separate calibrated model (for probabilities only)
est = DecisionTreeClassifier(max_depth=MAX_DEPTH, criterion="entropy", random_state=7)
cal = CalibratedClassifierCV(estimator=est, method="isotonic", cv=CV_FOLDS)
cal.fit(np.vstack([Xtr, Xva]), np.concatenate([ytr, yva]))

# Evaluate: use the TREE for accuracy vs teacher
pred_tree = tree.predict(Xte)
acc = accuracy_score(yte, pred_tree)

# Probabilities for Brier come from the calibrated model
proba_cal = cal.predict_proba(Xte)
brier = np.mean([
    brier_score_loss((yte == k).astype(int), proba_cal[:, k])
    for k in range(len(CLASSES))
])

bundle = {
    "tree": tree,                 # class decisions
    "cal": cal,                   # probability calibration
    "classes": CLASSES,
    "feature_order": FEATURE_ORDER,
    "version": VERSION,
}
out_path = REG / f"recommender_{VERSION}.joblib"
joblib.dump(bundle, out_path)

card = {
    "version": VERSION,
    "max_depth": MAX_DEPTH,
    "calib_cv": CV_FOLDS,
    "accuracy_vs_teacher_test": float(acc),
    "brier_mean_ovr": float(brier),
    "classes": CLASSES,
    "n_train": int(len(Xtr)), "n_val": int(len(Xva)), "n_test": int(len(Xte))
}
(Path("training/model_registry/model_card.json")
 .write_text(json.dumps(card, indent=2)))

print(f"Saved {out_path}  acc={acc:.3f}  brier≈{brier:.3f}")
assert acc >= 0.95, "Acceptance: accuracy vs teacher must be ≥ 0.95"
