import logging
import tempfile
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any

from fastapi import FastAPI, File, Form, UploadFile
from fastapi.responses import JSONResponse

from app.config import get_settings
from app.pipeline.errors import PipelineError
from app.pipeline.runner import PipelineOptions, run_pipeline

PHASE = 5
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_app: FastAPI):
    get_settings().ensure_data_dirs()
    yield


app = FastAPI(title="photo-ai orchestrator", lifespan=lifespan)


@app.exception_handler(PipelineError)
def pipeline_error_handler(_request: Any, exc: PipelineError) -> JSONResponse:
    return JSONResponse(
        status_code=500,
        content={
            "status": "failed",
            "failed_stage": exc.failed_stage,
            "detail": str(exc),
            "artifacts": exc.artifacts,
        },
    )


@app.get("/health")
def health() -> dict[str, Any]:
    settings = get_settings()
    data_ok = settings.data_dir.is_dir() and all(
        p.is_dir() for p in settings.data_subdirs()
    )
    return {
        "status": "ok" if data_ok else "degraded",
        "phase": PHASE,
        "pipeline_mode": settings.pipeline_mode,
        "data_dir": str(settings.data_dir),
        "data_dirs_ready": data_ok,
    }


@app.post("/api/v1/enhance")
async def enhance(
    file: UploadFile = File(...),
    pipeline_mode: str | None = Form(default=None),
    denoise: float | None = Form(default=None),
    seed: int | None = Form(default=None),
) -> dict[str, Any]:
    settings = get_settings()
    suffix = Path(file.filename or "upload.jpg").suffix or ".jpg"

    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
        tmp.write(await file.read())
        input_path = Path(tmp.name)

    try:
        result = run_pipeline(
            input_path,
            settings,
            PipelineOptions(
                mode=pipeline_mode or settings.pipeline_mode,
                denoise=denoise if denoise is not None else settings.pipeline_denoise,
                seed=seed if seed is not None else settings.sd_seed,
            ),
        )
    finally:
        input_path.unlink(missing_ok=True)

    return {
        "status": "completed",
        "output_path": str(result.output_path),
        "artifacts": result.artifacts,
        "duration_ms": result.duration_ms,
    }


@app.post("/api/v1/stages/rembg")
async def stage_rembg(file: UploadFile = File(...)) -> dict[str, str]:
    from app.pipeline.runner import run_rembg_stage

    settings = get_settings()
    stem = Path(file.filename or "upload").stem
    output_path = settings.stage1_nobg_dir / f"{stem}.png"

    suffix = Path(file.filename or "upload.jpg").suffix or ".jpg"
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
        tmp.write(await file.read())
        input_path = Path(tmp.name)

    try:
        run_rembg_stage(
            input_path,
            output_path,
            model=settings.rembg_model,
            model_dir=settings.rembg_model_dir,
        )
    finally:
        input_path.unlink(missing_ok=True)

    return {"output_path": str(output_path)}
