from dataclasses import dataclass
from datetime import datetime
from typing import Protocol


@dataclass(frozen=True)
class PresignedUrl:
    url: str
    expires_at: datetime


@dataclass(frozen=True)
class StoredObject:
    size: int
    content_type: str | None


class ObjectStorage(Protocol):
    def create_upload_url(self, object_key: str, content_type: str) -> PresignedUrl: ...

    def get_object_info(self, object_key: str) -> StoredObject | None: ...

    def create_download_url(self, object_key: str) -> PresignedUrl: ...
