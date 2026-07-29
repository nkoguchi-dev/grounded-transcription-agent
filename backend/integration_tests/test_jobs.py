import os
import time
from typing import cast

import httpx

BASE_URL = os.getenv("INTEGRATION_BASE_URL", "http://localhost:8010")


def _wait_for_terminal_status(job_id: str) -> dict[str, object]:
    deadline = time.monotonic() + 15
    with httpx.Client(base_url=BASE_URL) as client:
        while time.monotonic() < deadline:
            response = client.get(f"/api/jobs/{job_id}")
            response.raise_for_status()
            body = response.json()
            if body["status"] in {"succeeded", "failed"}:
                return cast(dict[str, object], body)
            time.sleep(0.2)
    raise AssertionError("job did not reach a terminal state")


def test_successful_job_runs_through_the_worker() -> None:
    with httpx.Client(base_url=BASE_URL) as client:
        response = client.post(
            "/api/jobs", json={"duration_seconds": 0, "should_fail": False}
        )
        assert response.status_code == 202
        job_id = response.json()["id"]
    result = _wait_for_terminal_status(job_id)
    assert result["status"] == "succeeded"
    assert result["result"] == {"message": "Dummy job completed"}


def test_failed_job_exposes_error() -> None:
    with httpx.Client(base_url=BASE_URL) as client:
        response = client.post(
            "/api/jobs", json={"duration_seconds": 0, "should_fail": True}
        )
        assert response.status_code == 202
        job_id = response.json()["id"]
    result = _wait_for_terminal_status(job_id)
    assert result["status"] == "failed"
    assert result["error_message"] == "Dummy job was configured to fail"
