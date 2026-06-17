"""
Async inference job queue — eliminates 504s on slow ML corrector.

Flow:
  POST /rewrite/async  → enqueue job, return {"job_id": "...", "status": "queued"} immediately
  GET  /rewrite/status/{job_id} → poll until status="done" | "error", then read result

Single asyncio.Queue + one background worker task. Worker processes jobs one at a time
so the ML model (loaded once, not thread-safe) is never called concurrently.
In-process — no Redis/Celery required. Survives App Runner single-container deploy.

Job TTL: results kept for 5 minutes then evicted to prevent memory leak.
"""
from __future__ import annotations

import asyncio
import logging
import time
import uuid
from typing import Any, Optional

logger = logging.getLogger(__name__)

# ── Job state ────────────────────────────────────────────────────────────────

_JOB_TTL_SECONDS = 300  # 5 minutes

class Job:
    __slots__ = ("id", "request", "status", "result", "error", "created_at", "done_at")

    def __init__(self, request: dict) -> None:
        self.id         = str(uuid.uuid4())
        self.request    = request
        self.status     = "queued"   # queued | processing | done | error
        self.result: Optional[dict] = None
        self.error:  Optional[str]  = None
        self.created_at = time.monotonic()
        self.done_at:   Optional[float] = None


# ── In-process store + queue ─────────────────────────────────────────────────

_jobs: dict[str, Job] = {}
_queue: asyncio.Queue[Job] = asyncio.Queue()


def enqueue(request: dict) -> Job:
    job = Job(request)
    _jobs[job.id] = job
    _queue.put_nowait(job)
    return job


def get_job(job_id: str) -> Optional[Job]:
    return _jobs.get(job_id)


def _evict_stale() -> None:
    now = time.monotonic()
    stale = [
        jid for jid, j in _jobs.items()
        if j.done_at and (now - j.done_at) > _JOB_TTL_SECONDS
    ]
    for jid in stale:
        del _jobs[jid]


# ── Worker ────────────────────────────────────────────────────────────────────

async def _worker() -> None:
    """Single background coroutine — processes jobs serially so ML model is never re-entrant."""
    logger.info("Async inference worker started")
    while True:
        job = await _queue.get()
        job.status = "processing"
        try:
            # Run the blocking service call in a thread so the event loop stays responsive
            result = await asyncio.get_event_loop().run_in_executor(
                None, _run_service, job.request
            )
            job.result = result
            job.status = "done"
        except Exception as exc:
            logger.exception("Job %s failed", job.id)
            job.error  = str(exc)
            job.status = "error"
        finally:
            job.done_at = time.monotonic()
            _queue.task_done()
            _evict_stale()


def _run_service(request: dict) -> dict:
    """Blocking call to rewrite service — runs in thread executor."""
    from .service import rewrite_text as service_rewrite
    response, audit_info = service_rewrite(
        id=request["id"],
        text=request["text"],
        lang=request["lang"],
        flags=request.get("flags"),
        region_dialect=request.get("region_dialect"),
        caller=request.get("caller"),
    )
    return {"response": response.model_dump(), "audit_info": audit_info}


# ── Lifecycle ─────────────────────────────────────────────────────────────────

_worker_task: Optional[asyncio.Task] = None


def start_worker() -> None:
    global _worker_task
    _worker_task = asyncio.get_event_loop().create_task(_worker())
    logger.info("Job queue worker task created")


def stop_worker() -> None:
    if _worker_task:
        _worker_task.cancel()
