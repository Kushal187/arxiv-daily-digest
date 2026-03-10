from __future__ import annotations

from datetime import date, datetime, timezone
from typing import Any

from fastapi import Depends, FastAPI, Header, HTTPException, Query
from pydantic import BaseModel

from .config import settings
from .db import get_connection
from .services.ingest import run_daily_ingest
from .services.ranking import build_digest_response, build_paper_response

app = FastAPI(title="arXiv Daily Digest Worker")


class DailyIngestRequest(BaseModel):
    runDate: date | None = None
    force: bool = False


def require_internal_token(authorization: str | None = Header(default=None)) -> None:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing bearer token")

    token = authorization.removeprefix("Bearer ").strip()
    valid_tokens = {settings.worker_internal_token, settings.ingest_job_token} - {""}
    if token not in valid_tokens:
        raise HTTPException(status_code=403, detail="Invalid token")


@app.get("/internal/health")
def health() -> dict[str, Any]:
    return {"ok": True, "timestamp": datetime.now(timezone.utc).isoformat()}


@app.post("/internal/jobs/daily-ingest", dependencies=[Depends(require_internal_token)])
def daily_ingest(payload: DailyIngestRequest) -> dict[str, Any]:
    result = run_daily_ingest(run_date=payload.runDate, force=payload.force)
    return result


@app.get("/internal/recommendations/digest", dependencies=[Depends(require_internal_token)])
def digest(
    user_id: str = Query(alias="userId"),
    digest_date: date = Query(alias="date"),
) -> dict[str, Any]:
    with get_connection() as connection:
        return build_digest_response(connection, user_id=user_id, digest_date=digest_date)


@app.get("/internal/papers/{paper_id}", dependencies=[Depends(require_internal_token)])
def paper_detail(paper_id: str, user_id: str = Query(alias="userId")) -> dict[str, Any]:
    with get_connection() as connection:
        payload = build_paper_response(connection, user_id=user_id, paper_id=paper_id)
        if not payload["paper"]:
            raise HTTPException(status_code=404, detail="Paper not found")

        return payload
