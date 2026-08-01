from typing import Protocol


class JobPublisher(Protocol):
    """Publish a job or raise a queue-agnostic JobDispatchError."""

    def publish(self, job_id: str) -> str: ...
