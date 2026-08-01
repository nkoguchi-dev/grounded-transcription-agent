from datetime import datetime, timedelta, timezone
from typing import Any

import boto3
from botocore.client import Config
from botocore.exceptions import BotoCoreError, ClientError

from app.application.artifacts.errors import ObjectStorageUnavailableError
from app.application.artifacts.object_storage import (
    ObjectStorage,
    PresignedUrl,
    StoredObject,
)


class S3ObjectStorage(ObjectStorage):
    def __init__(
        self,
        *,
        internal_endpoint: str,
        public_endpoint: str,
        access_key: str,
        secret_key: str,
        bucket: str,
        region: str,
        url_expiry_seconds: int = 900,
    ) -> None:
        common: dict[str, Any] = {
            "aws_access_key_id": access_key,
            "aws_secret_access_key": secret_key,
            "region_name": region,
            "config": Config(signature_version="s3v4", s3={"addressing_style": "path"}),
        }
        # The public client signs the externally reachable host directly. Rewriting
        # the host after signing would invalidate SigV4 verification.
        self._internal = boto3.client("s3", endpoint_url=internal_endpoint, **common)
        self._public = boto3.client("s3", endpoint_url=public_endpoint, **common)
        self._bucket = bucket
        self._url_expiry_seconds = url_expiry_seconds

    def _expiry(self) -> datetime:
        return datetime.now(timezone.utc) + timedelta(seconds=self._url_expiry_seconds)

    def create_upload_url(self, object_key: str, content_type: str) -> PresignedUrl:
        try:
            url = self._public.generate_presigned_url(
                "put_object",
                Params={
                    "Bucket": self._bucket,
                    "Key": object_key,
                    "ContentType": content_type,
                },
                ExpiresIn=self._url_expiry_seconds,
            )
        except (BotoCoreError, ClientError) as error:
            raise ObjectStorageUnavailableError() from error
        return PresignedUrl(url, self._expiry())

    def get_object_info(self, object_key: str) -> StoredObject | None:
        try:
            response = self._internal.head_object(Bucket=self._bucket, Key=object_key)
        except ClientError as error:
            code = error.response.get("Error", {}).get("Code")
            if code in {"404", "NoSuchKey", "NotFound"}:
                return None
            raise ObjectStorageUnavailableError() from error
        except BotoCoreError as error:
            raise ObjectStorageUnavailableError() from error
        return StoredObject(
            size=int(response["ContentLength"]),
            content_type=response.get("ContentType"),
        )

    def create_download_url(self, object_key: str) -> PresignedUrl:
        try:
            url = self._public.generate_presigned_url(
                "get_object",
                Params={"Bucket": self._bucket, "Key": object_key},
                ExpiresIn=self._url_expiry_seconds,
            )
        except (BotoCoreError, ClientError) as error:
            raise ObjectStorageUnavailableError() from error
        return PresignedUrl(url, self._expiry())
