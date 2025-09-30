api-recommender:
    uvicorn services.recommender_api.app:app -reload --reload-dir services/recommender_api --port 8014

api-context:
    uvicorn services.context_api.app:app --reload --reload-dir services/context_api --port 8012

smoke:
    ./scripts/smoke_local.sh
