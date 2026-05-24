from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Phase 1
    data_dir: Path = Field(default=Path("/data"), validation_alias="DATA_DIR")
    log_level: str = Field(default="info", validation_alias="LOG_LEVEL")

    # Phase 2+
    rembg_model: str = Field(default="u2net_cloth_seg", validation_alias="REMBG_MODEL")
    pipeline_upscale: int = Field(default=2, validation_alias="PIPELINE_UPSCALE")
    pipeline_denoise: float = Field(default=0.30, validation_alias="PIPELINE_DENOISE")
    pipeline_mode: str = Field(default="full", validation_alias="PIPELINE_MODE")

    # Phase 4+
    comfyui_url: str = Field(
        default="http://comfyui:8188", validation_alias="COMFYUI_URL"
    )
    workflow_polish_path: Path = Field(
        default=Path("/workflows/polish_catalog.json"),
        validation_alias="WORKFLOW_POLISH_PATH",
    )
    comfyui_timeout_sec: int = Field(default=120, validation_alias="COMFYUI_TIMEOUT_SEC")

    # SD (Phase 5+)
    sd_checkpoint: str = Field(
        default="realisticVision_v51.safetensors", validation_alias="SD_CHECKPOINT"
    )
    sd_steps: int = Field(default=20, validation_alias="SD_STEPS")
    sd_cfg: float = Field(default=7.0, validation_alias="SD_CFG")
    sd_sampler: str = Field(default="dpmpp_2m_sde", validation_alias="SD_SAMPLER")
    sd_seed: int = Field(default=-1, validation_alias="SD_SEED")

    # Phase 6+
    redis_url: str = Field(default="redis://redis:6379/0", validation_alias="REDIS_URL")
    max_concurrent_jobs: int = Field(default=1, validation_alias="MAX_CONCURRENT_JOBS")
    job_ttl_days: int = Field(default=7, validation_alias="JOB_TTL_DAYS")

    # Phase 7+
    min_short_edge_px: int = Field(default=512, validation_alias="MIN_SHORT_EDGE_PX")
    max_upload_mb: int = Field(default=30, validation_alias="MAX_UPLOAD_MB")
    api_key: str | None = Field(default=None, validation_alias="API_KEY")

    @property
    def input_dir(self) -> Path:
        return self.data_dir / "input"

    @property
    def output_dir(self) -> Path:
        return self.data_dir / "output"

    @property
    def stage1_nobg_dir(self) -> Path:
        return self.data_dir / "stage1_nobg"

    @property
    def stage2_upscale_dir(self) -> Path:
        return self.data_dir / "stage2_upscale"

    @property
    def stage3_sd_dir(self) -> Path:
        return self.data_dir / "stage3_sd"

    @property
    def models_dir(self) -> Path:
        return self.data_dir / "models"

    @property
    def rembg_model_dir(self) -> Path:
        return self.models_dir / "rembg"

    @property
    def realesrgan_weights_path(self) -> Path:
        return self.models_dir / "realesrgan" / "RealESRGAN_x4plus.pth"

    def data_subdirs(self) -> tuple[Path, ...]:
        return (
            self.input_dir,
            self.output_dir,
            self.stage1_nobg_dir,
            self.stage2_upscale_dir,
            self.stage3_sd_dir,
            self.models_dir,
        )

    def ensure_data_dirs(self) -> None:
        for path in self.data_subdirs():
            path.mkdir(parents=True, exist_ok=True)
        self.rembg_model_dir.mkdir(parents=True, exist_ok=True)


@lru_cache
def get_settings() -> Settings:
    return Settings()
