import pytest

from app.domain.artifacts.model import Artifact, ArtifactStatus


def test_artifact_uses_server_generated_opaque_object_key() -> None:
    artifact = Artifact.create("application/octet-stream", 12)

    assert artifact.status is ArtifactStatus.PENDING
    assert artifact.id in artifact.object_key
    assert artifact.object_key.startswith("artifacts/")
    assert artifact.actual_size is None


@pytest.mark.parametrize("expected_size", [-1, -100])
def test_artifact_rejects_negative_expected_size(expected_size: int) -> None:
    with pytest.raises(ValueError):
        Artifact.create("application/octet-stream", expected_size)


def test_completing_ready_artifact_is_idempotent() -> None:
    completed = Artifact.create("text/plain", 4).complete(4)

    assert completed.complete(999) == completed
