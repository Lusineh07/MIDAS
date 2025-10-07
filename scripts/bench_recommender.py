import os, time, statistics as stats, sys, pathlib
from fastapi.testclient import TestClient

# ensure repo root on sys.path
ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from services.recommender_api.app import app  # noqa: E402

# pin threads for stable timings
for k in ("OMP_NUM_THREADS","OPENBLAS_NUM_THREADS","MKL_NUM_THREADS","NUMEXPR_NUM_THREADS"):
    os.environ.setdefault(k, "1")

client = TestClient(app)
payload = {
    "sent_mean": 0.21, "sent_std": 0.08,
    "r_1m": 0.003, "r_5m": 0.001,
    "above_sma20": True, "mins_since_news": 12,
    "rv20": 0.18, "earnings_soon": False,
    "liquidity_flag": True
}

# warmup
for _ in range(50):
    assert client.post("/api/recommend", json=payload).status_code == 200

# sample
n = 300
xs = []
for _ in range(n):
    t0 = time.perf_counter_ns()
    r = client.post("/api/recommend", json=payload)
    assert r.status_code == 200, r.text
    xs.append((time.perf_counter_ns() - t0) / 1e6)

xs.sort()
p50 = stats.median(xs)
p95 = xs[int(0.95 * n) - 1]
print(f"p50={p50:.2f} ms  p95={p95:.2f} ms")