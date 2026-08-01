from typing import Annotated

from fastapi import APIRouter, Depends

from app.application.artifacts.complete_upload import CompleteUploadUseCase
from app.presentation.api.artifacts.artifact_response import ArtifactResponse

router = APIRouter(prefix="/api/artifacts", tags=["artifacts"])


def get_complete_upload_use_case() -> CompleteUploadUseCase:
    raise RuntimeError("CompleteUploadUseCase dependency is not configured")


@router.post("/{artifact_id}/complete", response_model=ArtifactResponse)
def complete_upload(
    artifact_id: str,
    use_case: Annotated[CompleteUploadUseCase, Depends(get_complete_upload_use_case)],
) -> ArtifactResponse:
    return ArtifactResponse.from_artifact(use_case.execute(artifact_id))
