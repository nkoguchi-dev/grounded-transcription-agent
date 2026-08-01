from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.application.artifacts.create_download_url import CreateDownloadUrlUseCase

router = APIRouter(prefix="/api/artifacts", tags=["artifacts"])


class DownloadUrlResponse(BaseModel):
    download_url: str
    expires_at: datetime


def get_create_download_url_use_case() -> CreateDownloadUrlUseCase:
    raise RuntimeError("CreateDownloadUrlUseCase dependency is not configured")


@router.post("/{artifact_id}/download-url", response_model=DownloadUrlResponse)
def create_download_url(
    artifact_id: str,
    use_case: Annotated[
        CreateDownloadUrlUseCase, Depends(get_create_download_url_use_case)
    ],
) -> DownloadUrlResponse:
    output = use_case.execute(artifact_id)
    return DownloadUrlResponse(download_url=output.url, expires_at=output.expires_at)
