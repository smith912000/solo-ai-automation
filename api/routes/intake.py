import os
from typing import Optional
from datetime import datetime

from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel, EmailStr

from lib import db as db_lib
from lib.auth import require_api_key


router = APIRouter(prefix="/webhook", tags=["intake"])


class LeadIntakeRequest(BaseModel):
    name: str
    email: EmailStr
    company: Optional[str] = None
    website: Optional[str] = None
    message: Optional[str] = None
    source: Optional[str] = None
    timestamp: Optional[str] = None


@router.post("/lead", status_code=202)
def intake_lead(
    payload: LeadIntakeRequest,
    x_client_id: Optional[str] = Header(default=None),
    x_api_key: Optional[str] = Header(default=None),
):
    require_api_key(x_api_key)
    client_id = x_client_id or os.getenv("DEFAULT_CLIENT_ID")
    if not client_id:
        raise HTTPException(status_code=500, detail="DEFAULT_CLIENT_ID is not set")

    email = db_lib.normalize_email(payload.email)
    timestamp = payload.timestamp or datetime.utcnow().isoformat()

    blocked_domains = os.getenv("PREFILTER_BLOCKED_DOMAINS", "")
    if blocked_domains:
        domain = email.split("@")[-1]
        blocked = [d.strip().lower() for d in blocked_domains.split(",") if d.strip()]
        if domain in blocked:
            return {"status": "filtered", "reason": "blocked_domain"}

    idempotency_key = db_lib.compute_idempotency_key(email, timestamp, payload.source)

    db = db_lib.get_supabase_client()
    existing = db_lib.get_run_by_idempotency(db, idempotency_key)
    if existing:
        return {
            "status": "duplicate",
            "run_id": existing.get("id"),
            "idempotency_key": idempotency_key,
        }

    run = db_lib.create_run(
        db,
        client_id=client_id,
        idempotency_key=idempotency_key,
        lead_email=email,
        trigger_payload=payload.dict(),
        status="queued",
    )

    job_payload = payload.dict()
    job_payload["email"] = email
    job_payload["timestamp"] = timestamp
    job_payload["run_id"] = run.get("id")
    job_payload["idempotency_key"] = idempotency_key

    job = db_lib.enqueue_job(
        db,
        client_id=client_id,
        lead_email=email,
        payload=job_payload,
    )

    return {
        "status": "queued",
        "run_id": run.get("id"),
        "job_id": job.get("id"),
        "idempotency_key": idempotency_key,
    }
