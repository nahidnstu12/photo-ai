class StageError(Exception):
    """Stage failed; message should be actionable."""


class PipelineError(StageError):
    """Pipeline failed at a stage; prior artifacts are left on disk."""

    def __init__(
        self,
        message: str,
        *,
        failed_stage: str,
        artifacts: dict[str, str] | None = None,
    ) -> None:
        super().__init__(message)
        self.failed_stage = failed_stage
        self.artifacts = artifacts or {}
