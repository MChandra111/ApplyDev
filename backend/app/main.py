"""FastAPI application entrypoint for ApplyDev."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import router as api_router
from app.config import configure_langsmith, configure_logging, load_project_env


@asynccontextmanager
async def lifespan(_app: FastAPI):
    """Load env and tracing once at startup."""
    load_project_env()
    configure_logging()
    configure_langsmith()
    yield


app = FastAPI(
    title="ApplyDev API",
    description="Multi-agent job application research system",
    version="0.2.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)


@app.get("/health")
async def health() -> dict[str, str]:
    """Return service health for load balancers and Docker health checks."""
    return {"status": "ok", "service": "applydev-backend"}

