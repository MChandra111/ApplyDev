"""In-memory job results for completed analyses (Phase 4)."""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from threading import Lock
from typing import Any
from uuid import uuid4


@dataclass
class JobRecord:
    """One analysis run keyed by job_id."""

    job_id: str
    job_url: str
    status: str  # running | completed | failed
    created_at: str
    result: dict[str, Any] | None = None
    error: str | None = None
    events: list[dict[str, Any]] = field(default_factory=list)


class JobStore:
    """Thread-safe store for job status and final pipeline state."""

    def __init__(self) -> None:
        """Initialize an empty in-memory job table."""
        self._jobs: dict[str, JobRecord] = {}
        self._lock = Lock()

    def create(self, job_url: str) -> JobRecord:
        """Register a new running job and return its record."""
        job_id = str(uuid4())
        record = JobRecord(
            job_id=job_id,
            job_url=job_url,
            status="running",
            created_at=datetime.now(timezone.utc).isoformat(),
        )
        with self._lock:
            self._jobs[job_id] = record
        return record

    def get(self, job_id: str) -> JobRecord | None:
        """Return a job record if it exists."""
        with self._lock:
            return self._jobs.get(job_id)

    def append_event(self, job_id: str, event: dict[str, Any]) -> None:
        """Append one SSE event to the job history."""
        with self._lock:
            record = self._jobs.get(job_id)
            if record:
                record.events.append(event)

    def complete(self, job_id: str, result: dict[str, Any]) -> None:
        """Mark a job completed and persist final pipeline state."""
        with self._lock:
            record = self._jobs.get(job_id)
            if record:
                record.status = "completed"
                record.result = result
                record.error = None

    def fail(self, job_id: str, error: str) -> None:
        """Mark a job failed with an error message."""
        with self._lock:
            record = self._jobs.get(job_id)
            if record:
                record.status = "failed"
                record.error = error


job_store = JobStore()
