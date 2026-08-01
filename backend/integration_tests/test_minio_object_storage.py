from collections.abc import Generator

import boto3
import httpx
import pytest
from botocore.client import Config
from testcontainers.core.container import DockerContainer

from app.infrastructure.object_storage import S3ObjectStorage


@pytest.fixture(scope="module")
def minio_endpoint() -> Generator[str]:
    container = (
        DockerContainer("minio/minio:RELEASE.2025-09-07T16-13-09Z")
        .with_env("MINIO_ROOT_USER", "minioadmin")
        .with_env("MINIO_ROOT_PASSWORD", "minioadmin")
        .with_command("server /data")
        .with_exposed_ports(9000)
    )
    with container:
        endpoint = (
            f"http://{container.get_container_host_ip()}:"
            f"{container.get_exposed_port(9000)}"
        )
        client = boto3.client(
            "s3",
            endpoint_url=endpoint,
            aws_access_key_id="minioadmin",
            aws_secret_access_key="minioadmin",
            region_name="ap-northeast-1",
            config=Config(signature_version="s3v4", s3={"addressing_style": "path"}),
        )
        client.create_bucket(Bucket="integration-artifacts")
        yield endpoint


def test_presigned_put_head_and_get_round_trip(minio_endpoint: str) -> None:
    storage = S3ObjectStorage(
        internal_endpoint=minio_endpoint,
        public_endpoint=minio_endpoint,
        access_key="minioadmin",
        secret_key="minioadmin",
        bucket="integration-artifacts",
        region="ap-northeast-1",
    )
    contents = b"grounded artifact"

    upload = storage.create_upload_url("artifacts/test/object", "text/plain")
    response = httpx.put(
        upload.url, content=contents, headers={"content-type": "text/plain"}
    )
    response.raise_for_status()

    info = storage.get_object_info("artifacts/test/object")
    assert info is not None
    assert info.size == len(contents)
    assert info.content_type == "text/plain"

    download = storage.create_download_url("artifacts/test/object")
    response = httpx.get(download.url)
    response.raise_for_status()
    assert response.content == contents
