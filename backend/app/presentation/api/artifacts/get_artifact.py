from typing import Annotated

from fastapi import APIRouter, Depends

from app.application.artifacts.get_artifact import GetArtifactUseCase
from app.presentation.api.artifacts.artifact_response import ArtifactResponse

router = APIRouter(prefix="/api/artifacts", tags=["artifacts"])


def get_get_artifact_use_case() -> GetArtifactUseCase:
    raise RuntimeError("GetArtifactUseCase dependency is not configured")


@router.get("/{artifact_id}", response_model=ArtifactResponse)
def get_artifact(
    artifact_id: str,
    use_case: Annotated[GetArtifactUseCase, Depends(get_get_artifact_use_case)],
) -> ArtifactResponse:
    return ArtifactResponse.from_artifact(use_case.execute(artifact_id))
