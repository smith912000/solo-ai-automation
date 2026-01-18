import os
from typing import Optional

from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel, EmailStr

from lib import db as db_lib
from lib.auth import require_api_key
from lib.email import send_email


router = APIRouter(prefix="/admin", tags=["admin"])


class SuppressionCreateRequest(BaseModel):
    email: EmailStr
    reason: Optional[str] = None


class OutboxApproveRequest(BaseModel):
    approved_by: Optional[str] = None


class OutboxRejectRequest(BaseModel):
    reason: str


class OutboxSendRequest(BaseModel):
    send_provider: Optional[str] = "sendgrid"


class AutomationPauseRequest(BaseModel):
    paused_by: Optional[str] = None
    reason: Optional[str] = None


@router.get("/suppression")
def list_suppression(
    x_client_id: Optional[str] = Header(default=None),
    x_api_key: Optional[str] = Header(default=None),
):
    require_api_key(x_api_key, admin=True)
    client_id = x_client_id or os.getenv("DEFAULT_CLIENT_ID")
    if not client_id:
        raise HTTPException(status_code=500, detail="DEFAULT_CLIENT_ID is not set")
    db = db_lib.get_supabase_client()
    return {"items": db_lib.list_suppression(db, client_id)}


@router.post("/suppression")
def add_suppression(
    payload: SuppressionCreateRequest,
    x_client_id: Optional[str] = Header(default=None),
    x_api_key: Optional[str] = Header(default=None),
):
    require_api_key(x_api_key, admin=True)
    client_id = x_client_id or os.getenv("DEFAULT_CLIENT_ID")
    if not client_id:
        raise HTTPException(status_code=500, detail="DEFAULT_CLIENT_ID is not set")
    db = db_lib.get_supabase_client()
    record = db_lib.add_suppression(db, client_id, payload.email, payload.reason)
    return {"item": record}


@router.delete("/suppression/{suppression_id}")
def delete_suppression(
    suppression_id: str,
    x_client_id: Optional[str] = Header(default=None),
    x_api_key: Optional[str] = Header(default=None),
):
    require_api_key(x_api_key, admin=True)
    client_id = x_client_id or os.getenv("DEFAULT_CLIENT_ID")
    if not client_id:
        raise HTTPException(status_code=500, detail="DEFAULT_CLIENT_ID is not set")
    db = db_lib.get_supabase_client()
    db_lib.delete_suppression(db, suppression_id)
    return {"status": "deleted"}


@router.get("/outbox")
def list_outbox(
    status: Optional[str] = None,
    limit: int = 50,
    x_client_id: Optional[str] = Header(default=None),
    x_api_key: Optional[str] = Header(default=None),
):
    require_api_key(x_api_key, admin=True)
    client_id = x_client_id or os.getenv("DEFAULT_CLIENT_ID")
    if not client_id:
        raise HTTPException(status_code=500, detail="DEFAULT_CLIENT_ID is not set")
    db = db_lib.get_supabase_client()
    items = db_lib.list_outbox_emails(db, client_id, status=status, limit=limit)
    return {"items": items}


@router.post("/outbox/{outbox_id}/approve")
def approve_outbox(
    outbox_id: str,
    payload: OutboxApproveRequest,
    x_client_id: Optional[str] = Header(default=None),
    x_api_key: Optional[str] = Header(default=None),
):
    require_api_key(x_api_key, admin=True)
    client_id = x_client_id or os.getenv("DEFAULT_CLIENT_ID")
    if not client_id:
        raise HTTPException(status_code=500, detail="DEFAULT_CLIENT_ID is not set")
    db = db_lib.get_supabase_client()
    record = db_lib.get_outbox_email(db, client_id, outbox_id)
    if not record:
        raise HTTPException(status_code=404, detail="Outbox email not found")
    db_lib.update_outbox_status(db, outbox_id, "approved", approved_by=payload.approved_by)
    return {"status": "approved"}


@router.post("/outbox/{outbox_id}/reject")
def reject_outbox(
    outbox_id: str,
    payload: OutboxRejectRequest,
    x_client_id: Optional[str] = Header(default=None),
    x_api_key: Optional[str] = Header(default=None),
):
    require_api_key(x_api_key, admin=True)
    client_id = x_client_id or os.getenv("DEFAULT_CLIENT_ID")
    if not client_id:
        raise HTTPException(status_code=500, detail="DEFAULT_CLIENT_ID is not set")
    db = db_lib.get_supabase_client()
    record = db_lib.get_outbox_email(db, client_id, outbox_id)
    if not record:
        raise HTTPException(status_code=404, detail="Outbox email not found")
    db_lib.update_outbox_status(db, outbox_id, "rejected", rejected_reason=payload.reason)
    return {"status": "rejected"}


@router.post("/outbox/{outbox_id}/send")
def send_outbox(
    outbox_id: str,
    payload: OutboxSendRequest,
    x_client_id: Optional[str] = Header(default=None),
    x_api_key: Optional[str] = Header(default=None),
):
    require_api_key(x_api_key, admin=True)
    client_id = x_client_id or os.getenv("DEFAULT_CLIENT_ID")
    if not client_id:
        raise HTTPException(status_code=500, detail="DEFAULT_CLIENT_ID is not set")
    db = db_lib.get_supabase_client()
    record = db_lib.get_outbox_email(db, client_id, outbox_id)
    if not record:
        raise HTTPException(status_code=404, detail="Outbox email not found")
    if record.get("status") == "sent":
        return {"status": "sent"}

    response = send_email(
        record.get("to_email"),
        record.get("subject"),
        record.get("body"),
    )
    db_lib.mark_outbox_sent(db, outbox_id, payload.send_provider or "sendgrid", response)
    db_lib.record_email_sent(
        db,
        client_id,
        record.get("lead_id"),
        record.get("to_email"),
        record.get("subject"),
    )
    db_lib.update_lead_status(
        db,
        client_id=client_id,
        lead_id=record.get("lead_id"),
        lead_email=record.get("to_email"),
        status="contacted",
    )
    return {"status": "sent", "send_response": response}


@router.get("/automation/{automation_name}")
def get_automation_status(
    automation_name: str,
    x_client_id: Optional[str] = Header(default=None),
    x_api_key: Optional[str] = Header(default=None),
):
    require_api_key(x_api_key, admin=True)
    client_id = x_client_id or os.getenv("DEFAULT_CLIENT_ID")
    if not client_id:
        raise HTTPException(status_code=500, detail="DEFAULT_CLIENT_ID is not set")
    db = db_lib.get_supabase_client()
    status = db_lib.get_automation_status(db, client_id, automation_name)
    return {"item": status}


@router.post("/automation/{automation_name}/pause")
def pause_automation(
    automation_name: str,
    payload: AutomationPauseRequest,
    x_client_id: Optional[str] = Header(default=None),
    x_api_key: Optional[str] = Header(default=None),
):
    require_api_key(x_api_key, admin=True)
    client_id = x_client_id or os.getenv("DEFAULT_CLIENT_ID")
    if not client_id:
        raise HTTPException(status_code=500, detail="DEFAULT_CLIENT_ID is not set")
    db = db_lib.get_supabase_client()
    db_lib.set_automation_status(
        db,
        client_id=client_id,
        automation_name=automation_name,
        status="paused",
        paused_by=payload.paused_by,
        pause_reason=payload.reason,
    )
    return {"status": "paused"}


@router.post("/automation/{automation_name}/resume")
def resume_automation(
    automation_name: str,
    x_client_id: Optional[str] = Header(default=None),
    x_api_key: Optional[str] = Header(default=None),
):
    require_api_key(x_api_key, admin=True)
    client_id = x_client_id or os.getenv("DEFAULT_CLIENT_ID")
    if not client_id:
        raise HTTPException(status_code=500, detail="DEFAULT_CLIENT_ID is not set")
    db = db_lib.get_supabase_client()
    db_lib.set_automation_status(
        db,
        client_id=client_id,
        automation_name=automation_name,
        status="active",
    )
    return {"status": "active"}


@router.get("/metrics")
def get_metrics(
    x_client_id: Optional[str] = Header(default=None),
    x_api_key: Optional[str] = Header(default=None),
):
    require_api_key(x_api_key, admin=True)
    client_id = x_client_id or os.getenv("DEFAULT_CLIENT_ID")
    if not client_id:
        raise HTTPException(status_code=500, detail="DEFAULT_CLIENT_ID is not set")
    db = db_lib.get_supabase_client()
    return {
        "queue": db_lib.get_queue_counts(db),
        "outbox": db_lib.get_outbox_counts(db, client_id),
        "runs": db_lib.get_run_counts(db, client_id),
        "recent_runs": db_lib.list_recent_runs(db, client_id, limit=15),
    }
