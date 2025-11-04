#!/bin/bash
# MIDAS — Quick Local Setup Script

# 1. Create and activate virtual environment if not exists
if [ ! -d ".venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv .venv
fi
source .venv/bin/activate

# 2. Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt

# 3. Export environment variables
export LIVE_PROVIDERS=1
export CTX_URL=http://127.0.0.1:8012
export REC_URL=http://127.0.0.1:8014

# 4. Run all services concurrently
echo "Starting all APIs..."
uvicorn services.context_api.app:app --port 8012 &
uvicorn services.recommender_api.app:app --port 8014 &
uvicorn services.gateway_api.app:app --port 8015 &
uvicorn services.sentiment_api.app:app --port 8016 &

echo "MIDAS is running!"
echo "Ports:"
echo " - Context API:     http://127.0.0.1:8012"
echo " - Recommender API: http://127.0.0.1:8014"
echo " - Gateway API:     http://127.0.0.1:8015"
echo " - Sentiment API:   http://127.0.0.1:8016"
echo ""
echo "Frontend: run 'cd frontend && npm install && npm start' in a new terminal."
wait
