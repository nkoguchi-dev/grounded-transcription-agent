from typing import Protocol


class JobPublisher(Protocol):
    """Expose task publication without coupling application code to a queue product."""

    def publish(self, job_id: str) -> str: ...
