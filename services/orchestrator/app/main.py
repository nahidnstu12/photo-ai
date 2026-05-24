import logging
import tempfile
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any

from fastapi import FastAPI, File, UploadFile

from app.cli import _run_rembg_stage
from app.config import get_settings

PHASE = 3
logger = logging.getLogger(__name__)


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


@app.post("/api/v1/stages/rembg")
async def stage_rembg(file: UploadFile = File(...)) -> dict[str, str]:
    settings = get_settings()
    stem = Path(file.filename or "upload").stem
    output_path = settings.stage1_nobg_dir / f"{stem}.png"

    suffix = Path(file.filename or "upload.jpg").suffix or ".jpg"
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
        tmp.write(await file.read())
        input_path = Path(tmp.name)

    try:
        _run_rembg_stage(
            input_path,
            output_path,
            model=settings.rembg_model,
            model_dir=settings.rembg_model_dir,
        )
    finally:
        input_path.unlink(missing_ok=True)

    return {"output_path": str(output_path)}
