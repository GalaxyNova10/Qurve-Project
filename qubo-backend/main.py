import logging
from pathlib import Path
from fastapi import FastAPI
from contextlib import asynccontextmanager
from fastapi.middleware.cors import CORSMiddleware
from qubo_backend.config import get_settings
from qubo_backend.storage.artifacts import ArtifactStore
from qubo_backend.jobs.store import JobStore
from qubo_backend.api.routes import create_api_router, create_websocket_router
from qubo_backend.monitoring.monitoring_api import get_monitoring_overview
from qubo_backend.api.health import health_check as comprehensive_health
import auth

logging.basicConfig(level=logging.INFO)

settings = get_settings()

# Bootstrap: ensure required directories and data files exist
try:
    from bootstrap import bootstrap
    bootstrap_result = bootstrap(base_dir=Path(__file__).resolve().parent.parent, force=False)
    logging.info("Bootstrap completed: alpha_data=%s valid=%s", 
                 bootstrap_result.get("alpha_data_path"), 
                 bootstrap_result.get("alpha_data_valid"))
except Exception as e:
    logging.error("Bootstrap failed, server will start but benchmark may fail: %s", e)

artifacts = ArtifactStore(settings.output_dir)
job_store = JobStore(settings.jobs_dir)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup actions
    from qubo_backend.subscribers import register_subscribers
    register_subscribers()
    yield
    # Shutdown actions

app = FastAPI(title="QUBO Portfolio Optimizer", lifespan=lifespan)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Nuclear option for local debugging
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from qubo_backend.monitoring.monitoring_api import monitoring_router, get_monitoring_overview

api_router = create_api_router(settings, artifacts, job_store)
ws_router = create_websocket_router(settings)
app.include_router(api_router, prefix="/api/v1")
app.include_router(api_router, prefix="/api")
app.include_router(ws_router)
app.include_router(monitoring_router)
app.include_router(auth.router, prefix="/api/v1")
app.include_router(auth.router, prefix="/api")

@app.get("/health")
async def root_health():
    return await comprehensive_health()

@app.get("/api/monitoring")
async def root_monitoring():
    return await get_monitoring_overview()

if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host='0.0.0.0', port=8000, reload=False)

