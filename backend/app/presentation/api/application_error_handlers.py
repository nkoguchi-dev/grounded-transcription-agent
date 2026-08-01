from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse

from app.application.artifacts.errors import (
    ArtifactNotFoundError,
    ArtifactNotReadyError,
    ArtifactObjectNotFoundError,
    ObjectStorageUnavailableError,
)
from app.application.jobs.errors import JobDispatchError, JobNotFoundError


def register_application_error_handlers(app: FastAPI) -> None:
    """Keep public HTTP mappings explicit and separate from application errors."""

    @app.exception_handler(JobNotFoundError)
    async def handle_job_not_found(
        _request: Request, _error: JobNotFoundError
    ) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={"detail": "Job not found"},
        )

    @app.exception_handler(JobDispatchError)
    async def handle_job_dispatch_failure(
        _request: Request, _error: JobDispatchError
    ) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={"detail": "Job broker is unavailable"},
        )

    @app.exception_handler(ArtifactNotFoundError)
    async def handle_artifact_not_found(
        _request: Request, _error: ArtifactNotFoundError
    ) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={"detail": "Artifact not found"},
        )

    @app.exception_handler(ArtifactObjectNotFoundError)
    async def handle_artifact_object_not_found(
        _request: Request, _error: ArtifactObjectNotFoundError
    ) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content={"detail": "Uploaded object not found"},
        )

    @app.exception_handler(ArtifactNotReadyError)
    async def handle_artifact_not_ready(
        _request: Request, _error: ArtifactNotReadyError
    ) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content={"detail": "Artifact is not ready"},
        )

    @app.exception_handler(ObjectStorageUnavailableError)
    async def handle_object_storage_unavailable(
        _request: Request, _error: ObjectStorageUnavailableError
    ) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={"detail": "Object storage is unavailable"},
        )
