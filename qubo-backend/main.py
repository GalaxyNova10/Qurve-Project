import logging
from fastapi import FastAPI
from qubo_backend.config import get_settings
from qubo_backend.storage.artifacts import ArtifactStore
from qubo_backend.jobs.store import JobStore
from qubo_backend.api.routes import create_api_router

logging.basicConfig(level=logging.INFO)

settings = get_settings()
artifacts = ArtifactStore(settings.output_dir)
job_store = JobStore(settings.jobs_dir)

app = FastAPI(title="QUBO Portfolio Optimizer")

api_router = create_api_router(settings, artifacts, job_store)
app.include_router(api_router)

if __name__ == '__main__':
    import uvicorn
    uvicorn.run('main:app', host='0.0.0.0', port=8000, reload=False)

