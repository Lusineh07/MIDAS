#training/synth_generate.py
import numpy as np, pandas as pd, os
from pathlib import Path
from rules_teacher import label_one, CLASSES

rng = np.random.default_rng(42)
N = int(os.environ.get("N_ROWS", 20000))

def sample(N):
    df = pd.DataFrame({
        "sent_mean": rng.uniform(-0.6, 0.6, N),
        "sent_std": rng.uniform(0.00, 0.40, N),
        "r_1m": rng.uniform(-0.05, 0.05, N),
        "r_5m": rng.uniform(-0.02, 0.02, N),
        "above_sma20": rng.integers(0, 2, N).astype(bool),
        "mins_since_news": rng.integers(0, 721, N),
        "rv20": rng.uniform(0.01, 0.80, N),
        "earnings_soon": rng.integers(0, 2, N).astype(bool),
        "liquidity_flag": rng.integers(0, 10, N) > 0 #~90% True
    })

    #simple correlation: big move = higher rv20
    bump = np.clip(np.abs(df["r_5m"]) / 0.02, 0, 1) * 0.10
    df["rv20"] = np.clip(df["rv20"] + bump, 0.01, 0.80)

    df["label"] = [label_one(row) for _, row in df.iterrows()]
    return df

df = sample(N)
#split 80/10/10 train/val/test
idx = rng.permutation(len(df))
n_train = int(0.8 * len(df)); n_val = int(0.1 * len(df))
train, val, test = df.iloc[idx[:n_train]], df.iloc[idx[n_train:n_train+n_val]], df.iloc[idx[n_train+n_val:]]

out = Path("training/data"); out.mkdir(parents=True, exist_ok=True)
train.to_parquet(out/"synthetic_train.parquet")
val.to_parquet(out/"synthetic_val.parquet")
test.to_parquet(out/"synthetic_test.parquet")

print("Class distribution:")
print(df["label"].value_counts(normalize=True).reindex(CLASSES).fillna(0).round(3))