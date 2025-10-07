#!/usr/bin/env bash
set -euo pipefail
echo "Context health:" && curl -s http://127.0.0.1:8012/healthz | jq .
echo "Recommender health:" && curl -s http://127.0.0.1:8014/healthz | jq .
curl -s 'http://127.0.0.1:8012/api/features?ticker=NVDA' | jq -c '.features' >/tmp/features.json
echo "Features payload to recommender:" && cat /tmp/features.json
echo "Recommendation:" && curl -s -X POST 'http://127.0.0.1:8014/api/recommend' \
  -H 'content-type: application/json' --data-binary @/tmp/features.json | jq .
