import time
from fastapi.testclient import TestClient
from services.recommender_api.app import app

client = TestClient(app)

PAYLOAD = {
    "sent_mean": 0.21, "sent_std": 0.08,
    "r_1m": 0.003, "r_5m": 0.001,
    "above_sma20": True, "mins_since_news": 12,
    "rv20": 0.18, "earnings_soon": False,
    "liquidity_flag": True
}

def test_latency_p95_under_5ms():
    times_ms = []
    # warmup
    for _ in range(20):
        r = client.post("/api/recommend", json=PAYLOAD)
        assert r.status_code == 200
    # sample
    for _ in range(200):
        t0 = time.perf_counter_ns()
        r = client.post("/api/recommend", json=PAYLOAD)
        assert r.status_code == 200, r.text
        times_ms.append((time.perf_counter_ns() - t0) / 1e6)
    times_ms.sort()
    p95 = times_ms[int(0.95 * len(times_ms)) - 1]
    assert p95 < 5.0, f"p95={p95:.3f} ms"
