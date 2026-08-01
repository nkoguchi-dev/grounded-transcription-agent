from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, status
from pydantic import BaseModel, ConfigDict, Field

from app.application.artifacts.start_upload import StartUploadInput, StartUploadUseCase

router = APIRouter(prefix="/api/artifacts/uploads", tags=["artifacts"])


class StartUploadRequest(BaseModel):
    model_config = ConfigDict(strict=True, extra="forbid")
    content_type: str = Field(min_length=1, max_length=255, pattern=r".*\S.*")
    expected_size: int = Field(ge=0)


class StartUploadResponse(BaseModel):
    artifact_id: str
    status: str
    upload_url: str
    expires_at: datetime


def get_start_upload_use_case() -> StartUploadUseCase:
    raise RuntimeError("StartUploadUseCase dependency is not configured")


@router.post(
    "", response_model=StartUploadResponse, status_code=status.HTTP_201_CREATED
)
def start_upload(
    request: StartUploadRequest,
    use_case: Annotated[StartUploadUseCase, Depends(get_start_upload_use_case)],
) -> StartUploadResponse:
    output = use_case.execute(
        StartUploadInput(request.content_type, request.expected_size)
    )
    return StartUploadResponse(
        artifact_id=output.artifact.id,
        status=output.artifact.status.value,
        upload_url=output.upload.url,
        expires_at=output.upload.expires_at,
    )
