import os, time, statistics as stats
from fastapi.testclient import TestClient
from services.recommender_api.app import app

# Make timings stable across machines/CI
os.environ.setdefault("OMP_NUM_THREADS", "1")
os.environ.setdefault("MKL_NUM_THREADS", "1")
os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
os.environ.setdefault("NUMEXPR_NUM_THREADS", "1")

client = TestClient(app)

PAYLOAD = {
    "sent_mean": 0.21, "sent_std": 0.08,
    "r_1m": 0.003, "r_5m": 0.001,
    "above_sma20": True, "mins_since_news": 12,
    "rv20": 0.18, "earnings_soon": False,
    "liquidity_flag": True
}

def test_latency_p95_reasonable():
    # Warm up the app & model
    for _ in range(50):
        r = client.post("/api/recommend", json=PAYLOAD)
        assert r.status_code == 200

    # Measure a decent number of calls
    n = 300
    samples = []
    for _ in range(n):
        t0 = time.perf_counter_ns()
        r = client.post("/api/recommend", json=PAYLOAD)
        assert r.status_code == 200, r.text
        samples.append((time.perf_counter_ns() - t0) / 1e6)

    samples.sort()
    p50 = stats.median(samples)
    p95 = samples[int(0.95 * n) - 1]

    # Adaptive bound: p95 should be close to the median, not 10x slower.
    # Also apply an absolute ceiling that we can tighten later.
    adaptive_limit = max(6.0, p50 * 3.0)   # typical is far below this; CI-safe
    hard_ceiling   = float(os.environ.get("RECOMMENDER_P95_MS", "40"))  # override in CI if desired

    assert p95 < adaptive_limit and p95 < hard_ceiling, f"p50={p50:.2f}ms p95={p95:.2f}ms (limit {adaptive_limit:.2f}ms, ceiling {hard_ceiling:.1f}ms)"