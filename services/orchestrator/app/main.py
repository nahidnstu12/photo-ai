from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI

from app.config import get_settings

PHASE = 1


@asynccontextmanager
async def lifespan(_app: FastAPI):
    get_settings().ensure_data_dirs()
    yield


app = FastAPI(title="photo-ai orchestrator", lifespan=lifespan)


@app.get("/health")
def health() -> dict[str, Any]:
    settings = get_settings()
    data_ok = settings.data_dir.is_dir() and all(
        p.is_dir() for p in settings.data_subdirs()
    )
    return {
        "status": "ok" if data_ok else "degraded",
        "phase": PHASE,
        "data_dir": str(settings.data_dir),
        "data_dirs_ready": data_ok,
    }
