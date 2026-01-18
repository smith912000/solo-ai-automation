"""
Supabase database access layer.
Centralizes all DB operations for intake + worker.
"""

import os
import hashlib
from typing import Optional, Any
from datetime import datetime, timedelta

from supabase import create_client, Client


def get_supabase_client() -> Client:
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_KEY")
    if not url or not key:
        raise ValueError("SUPABASE_URL and SUPABASE_KEY must be set")
    return create_client(url, key)


def normalize_email(email: str) -> str:
    return email.strip().lower()


def compute_idempotency_key(email: str, timestamp: Optional[str], source: Optional[str]) -> str:
    key_input = f"{email}:{timestamp or ''}:{source or ''}"
    return hashlib.sha256(key_input.encode()).hexdigest()[:32]


def get_run_by_idempotency(db: Client, idempotency_key: str) -> Optional[dict]:
    response = db.table("runs").select("*").eq("idempotency_key", idempotency_key).execute()
    if response.data:
        return response.data[0]
    return None


def create_run(
    db: Client,
    client_id: str,
    idempotency_key: str,
    lead_email: str,
    trigger_payload: dict,
    status: str = "queued",
) -> dict:
    response = db.table("runs").insert(
        {
            "client_id": client_id,
            "idempotency_key": idempotency_key,
            "lead_email": lead_email,
            "automation_name": "lead-qualifier",
            "trigger_type": "webhook",
            "trigger_payload": trigger_payload,
            "status": status,
        }
    ).execute()
    return response.data[0]


def update_run_status(db: Client, run_id: str, status: str, error_message: Optional[str] = None):
    payload = {"status": status}
    if error_message:
        payload["error_message"] = error_message
    db.table("runs").update(payload).eq("id", run_id).execute()


def upsert_lead(db: Client, client_id: str, lead: dict) -> dict:
    payload = {
        "client_id": client_id,
        "email": lead.get("email"),
        "name": lead.get("name"),
        "company": lead.get("company"),
        "website": lead.get("website"),
        "source": lead.get("source"),
        "raw_form_data": lead,
    }
    response = db.table("leads").upsert(payload, on_conflict="client_id,email").execute()
    return response.data[0]


def enqueue_job(
    db: Client,
    client_id: str,
    lead_email: str,
    payload: dict,
    next_run_at: Optional[str] = None,
    job_type: str = "lead_qualify",
    priority: int = 0,
    correlation_id: Optional[str] = None,
) -> dict:
    job_payload = {
        "client_id": client_id,
        "lead_email": lead_email,
        "payload": payload,
        "status": "queued",
        "job_type": job_type,
        "priority": priority,
    }
    if correlation_id:
        job_payload["correlation_id"] = correlation_id
    if next_run_at:
        job_payload["next_run_at"] = next_run_at
    response = db.table("jobs_queue").insert(job_payload).execute()
    return response.data[0]


def create_agent_task(
    db: Client,
    client_id: str,
    task_type: str,
    payload: Optional[dict] = None,
    priority: int = 0,
    assigned_agent: Optional[str] = None,
    correlation_id: Optional[str] = None,
) -> dict:
    task_payload = {
        "client_id": client_id,
        "task_type": task_type,
        "status": "queued",
        "priority": priority,
        "payload": payload or {},
    }
    if assigned_agent:
        task_payload["assigned_agent"] = assigned_agent
    if correlation_id:
        task_payload["correlation_id"] = correlation_id
    response = db.table("agent_tasks").insert(task_payload).execute()
    return response.data[0]


def update_agent_task_status(db: Client, task_id: str, status: str):
    db.table("agent_tasks").update({"status": status}).eq("id", task_id).execute()


def record_agent_run(
    db: Client,
    client_id: str,
    task_id: str,
    agent_name: str,
    status: str,
    input_json: Optional[dict] = None,
    output_json: Optional[dict] = None,
    error_message: Optional[str] = None,
    cost_estimate_usd: float = 0.0,
    duration_ms: Optional[int] = None,
):
    payload: dict[str, Any] = {
        "client_id": client_id,
        "task_id": task_id,
        "agent_name": agent_name,
        "status": status,
        "input_json": input_json or {},
        "output_json": output_json or {},
        "cost_estimate_usd": cost_estimate_usd,
        "started_at": datetime.utcnow().isoformat(),
    }
    if duration_ms is not None:
        payload["duration_ms"] = duration_ms
        payload["completed_at"] = datetime.utcnow().isoformat()
    if error_message:
        payload["error_message"] = error_message
    db.table("agent_runs").insert(payload).execute()


def create_voice_session(
    db: Client,
    client_id: str,
    crm_lead_id: Optional[str] = None,
    metadata: Optional[dict] = None,
    channel: str = "web",
) -> dict:
    payload = {
        "client_id": client_id,
        "channel": channel,
        "metadata": metadata or {},
    }
    if crm_lead_id:
        payload["crm_lead_id"] = crm_lead_id
    response = db.table("voice_sessions").insert(payload).execute()
    return response.data[0]


def get_voice_session(db: Client, session_id: str) -> Optional[dict]:
    response = db.table("voice_sessions").select("*").eq("id", session_id).execute()
    if response.data:
        return response.data[0]
    return None


def list_voice_turns(db: Client, session_id: str) -> list[dict]:
    response = (
        db.table("voice_turns")
        .select("*")
        .eq("session_id", session_id)
        .order("created_at", desc=False)
        .execute()
    )
    return response.data or []


def add_voice_turn(
    db: Client,
    session_id: str,
    role: str,
    content: str,
    action: Optional[str] = None,
    confidence: Optional[float] = None,
) -> dict:
    payload: dict[str, Any] = {
        "session_id": session_id,
        "role": role,
        "content": content,
    }
    if action:
        payload["action"] = action
    if confidence is not None:
        payload["confidence"] = confidence
    response = db.table("voice_turns").insert(payload).execute()
    return response.data[0]


def create_kpi_snapshot(
    db: Client,
    client_id: str,
    period_start: str,
    period_end: str,
    metrics: dict,
) -> dict:
    payload = {
        "client_id": client_id,
        "period_start": period_start,
        "period_end": period_end,
        "metrics": metrics,
    }
    response = db.table("kpi_snapshots").insert(payload).execute()
    return response.data[0]


def record_cost_event(
    db: Client,
    client_id: str,
    category: str,
    cost_usd: float,
    quantity: float = 0.0,
    unit_cost_usd: float = 0.0,
    provider: Optional[str] = None,
    automation_name: Optional[str] = None,
    run_id: Optional[str] = None,
    task_id: Optional[str] = None,
    metadata: Optional[dict] = None,
) -> dict:
    payload: dict[str, Any] = {
        "client_id": client_id,
        "category": category,
        "cost_usd": cost_usd,
        "quantity": quantity,
        "unit_cost_usd": unit_cost_usd,
        "metadata": metadata or {},
    }
    if provider:
        payload["provider"] = provider
    if automation_name:
        payload["automation_name"] = automation_name
    if run_id:
        payload["run_id"] = run_id
    if task_id:
        payload["task_id"] = task_id
    response = db.table("cost_events").insert(payload).execute()
    return response.data[0]


def list_cost_events(
    db: Client,
    client_id: str,
    start_at: Optional[str] = None,
    end_at: Optional[str] = None,
    category: Optional[str] = None,
    limit: int = 500,
) -> list[dict]:
    query = db.table("cost_events").select("*").eq("client_id", client_id)
    if category:
        query = query.eq("category", category)
    if start_at:
        query = query.gte("created_at", start_at)
    if end_at:
        query = query.lte("created_at", end_at)
    response = query.order("created_at", desc=True).limit(limit).execute()
    return response.data or []


def update_experiment(
    db: Client,
    experiment_id: str,
    status: Optional[str] = None,
    results: Optional[dict] = None,
):
    payload: dict[str, Any] = {}
    if status:
        payload["status"] = status
    if results is not None:
        payload["results"] = results
    if status in {"completed", "cancelled"}:
        payload["completed_at"] = datetime.utcnow().isoformat()
    if payload:
        db.table("experiments").update(payload).eq("id", experiment_id).execute()


def claim_next_job(db: Client, worker_id: str, lease_seconds: int) -> Optional[dict]:
    response = db.rpc(
        "claim_next_job",
        {"worker_id": worker_id, "lease_seconds": lease_seconds},
    ).execute()
    if response.data:
        return response.data[0]
    return None


def mark_job_done(db: Client, job_id: str, status: str, error_message: Optional[str] = None):
    payload = {"status": status, "locked_until": None, "locked_by": None}
    if error_message:
        payload["error_message"] = error_message
    db.table("jobs_queue").update(payload).eq("id", job_id).execute()


def requeue_job(db: Client, job_id: str, delay_seconds: int, error_message: Optional[str] = None):
    next_run_at = (datetime.utcnow() + timedelta(seconds=delay_seconds)).isoformat()
    payload = {
        "status": "queued",
        "locked_until": None,
        "locked_by": None,
        "next_run_at": next_run_at,
    }
    if error_message:
        payload["error_message"] = error_message
    db.table("jobs_queue").update(payload).eq("id", job_id).execute()


def is_email_suppressed(db: Client, client_id: str, email: str) -> bool:
    response = (
        db.table("suppression_list")
        .select("id")
        .eq("client_id", client_id)
        .eq("email", email)
        .execute()
    )
    return len(response.data) > 0


def add_suppression(db: Client, client_id: str, email: str, reason: Optional[str] = None) -> dict:
    payload = {"client_id": client_id, "email": email, "reason": reason}
    response = db.table("suppression_list").insert(payload).execute()
    return response.data[0]


def list_suppression(db: Client, client_id: str) -> list[dict]:
    response = db.table("suppression_list").select("*").eq("client_id", client_id).execute()
    return response.data or []


def delete_suppression(db: Client, suppression_id: str):
    db.table("suppression_list").delete().eq("id", suppression_id).execute()


def email_sent_recently(db: Client, client_id: str, email: str, days: int) -> bool:
    cutoff = (datetime.utcnow() - timedelta(days=days)).isoformat()
    response = (
        db.table("email_history")
        .select("id")
        .eq("client_id", client_id)
        .eq("lead_email", email)
        .gte("sent_at", cutoff)
        .execute()
    )
    return len(response.data) > 0


def record_email_sent(db: Client, client_id: str, lead_id: Optional[str], email: str, subject: str):
    payload = {
        "client_id": client_id,
        "lead_id": lead_id,
        "lead_email": email,
        "subject": subject,
        "automation_name": "lead-qualifier",
        "sent_at": datetime.utcnow().isoformat(),
    }
    db.table("email_history").insert(payload).execute()


def queue_email(
    db: Client,
    client_id: str,
    lead_id: Optional[str],
    run_id: Optional[str],
    to_email: str,
    to_name: str,
    subject: str,
    body: str,
) -> dict:
    payload = {
        "client_id": client_id,
        "lead_id": lead_id,
        "to_email": to_email,
        "to_name": to_name,
        "subject": subject,
        "body": body,
        "status": "queued",
    }
    if run_id:
        payload["run_id"] = run_id
    response = db.table("outbox_emails").insert(payload).execute()
    return response.data[0]


def list_outbox_emails(
    db: Client,
    client_id: str,
    status: Optional[str] = None,
    limit: int = 50,
) -> list[dict]:
    query = db.table("outbox_emails").select("*").eq("client_id", client_id)
    if status:
        query = query.eq("status", status)
    response = query.order("created_at", desc=True).limit(limit).execute()
    return response.data or []


def list_outbox_approved(
    db: Client,
    client_id: str,
    limit: int = 25,
) -> list[dict]:
    return list_outbox_emails(db, client_id, status="approved", limit=limit)


def get_outbox_email(db: Client, client_id: str, outbox_id: str) -> Optional[dict]:
    response = (
        db.table("outbox_emails")
        .select("*")
        .eq("client_id", client_id)
        .eq("id", outbox_id)
        .execute()
    )
    if response.data:
        return response.data[0]
    return None


def update_outbox_status(
    db: Client,
    outbox_id: str,
    status: str,
    approved_by: Optional[str] = None,
    rejected_reason: Optional[str] = None,
):
    payload: dict[str, Any] = {"status": status}
    if approved_by:
        payload["approved_by"] = approved_by
        payload["approved_at"] = datetime.utcnow().isoformat()
    if rejected_reason:
        payload["rejected_reason"] = rejected_reason
    db.table("outbox_emails").update(payload).eq("id", outbox_id).execute()


def mark_outbox_sent(
    db: Client,
    outbox_id: str,
    send_provider: str,
    send_response: dict,
):
    payload = {
        "status": "sent",
        "sent_at": datetime.utcnow().isoformat(),
        "send_provider": send_provider,
        "send_response": send_response,
    }
    db.table("outbox_emails").update(payload).eq("id", outbox_id).execute()


def update_lead_status(
    db: Client,
    client_id: str,
    lead_id: Optional[str],
    lead_email: Optional[str],
    status: str,
):
    if not lead_id and not lead_email:
        return
    query = db.table("leads").update({"status": status}).eq("client_id", client_id)
    if lead_id:
        query = query.eq("id", lead_id)
    if lead_email:
        query = query.eq("email", lead_email)
    query.execute()


def get_automation_status(db: Client, client_id: str, automation_name: str) -> dict:
    response = (
        db.table("automation_status")
        .select("*")
        .eq("client_id", client_id)
        .eq("automation_name", automation_name)
        .execute()
    )
    if response.data:
        return response.data[0]
    return {"status": "active"}


def set_automation_status(
    db: Client,
    client_id: str,
    automation_name: str,
    status: str,
    paused_by: Optional[str] = None,
    pause_reason: Optional[str] = None,
):
    payload = {
        "client_id": client_id,
        "automation_name": automation_name,
        "status": status,
    }
    if status == "paused":
        payload["paused_at"] = datetime.utcnow().isoformat()
        if paused_by:
            payload["paused_by"] = paused_by
        if pause_reason:
            payload["pause_reason"] = pause_reason
    db.table("automation_status").upsert(payload, on_conflict="client_id,automation_name").execute()


def get_outbox_counts(db: Client, client_id: str) -> dict:
    counts = {}
    for status in ["queued", "approved", "sent", "rejected"]:
        response = (
            db.table("outbox_emails")
            .select("id", count="exact")
            .eq("client_id", client_id)
            .eq("status", status)
            .execute()
        )
        counts[status] = response.count or 0
    return counts


def get_run_counts(db: Client, client_id: str) -> dict:
    counts = {}
    for status in ["pending", "success", "failed", "killed", "skipped"]:
        response = (
            db.table("runs")
            .select("id", count="exact")
            .eq("client_id", client_id)
            .eq("status", status)
            .execute()
        )
        counts[status] = response.count or 0
    return counts


def list_recent_runs(db: Client, client_id: str, limit: int = 20) -> list[dict]:
    response = (
        db.table("runs")
        .select(
            "id, lead_email, status, cost_estimate_usd, error_message, started_at, completed_at"
        )
        .eq("client_id", client_id)
        .order("started_at", desc=True)
        .limit(limit)
        .execute()
    )
    return response.data or []


def list_crm_leads(db: Client, client_id: str, limit: int = 100) -> list[dict]:
    response = (
        db.table("crm_leads")
        .select("*")
        .eq("client_id", client_id)
        .order("created_at", desc=True)
        .limit(limit)
        .execute()
    )
    return response.data or []


def list_agent_runs(
    db: Client,
    client_id: str,
    agent_name: Optional[str] = None,
    limit: int = 50,
) -> list[dict]:
    query = db.table("agent_runs").select("*").eq("client_id", client_id)
    if agent_name:
        query = query.eq("agent_name", agent_name)
    response = query.order("started_at", desc=True).limit(limit).execute()
    return response.data or []


def get_queue_depth(db: Client) -> int:
    response = db.table("jobs_queue").select("id", count="exact").eq("status", "queued").execute()
    return response.count or 0


def get_queue_counts(db: Client) -> dict:
    counts = {}
    for status in ["queued", "processing", "done", "failed", "dead"]:
        response = db.table("jobs_queue").select("id", count="exact").eq("status", status).execute()
        counts[status] = response.count or 0
    return counts


def update_lead_qualification(
    db: Client,
    client_id: str,
    email: str,
    qualification: dict,
    enrichment: Optional[dict] = None,
):
    payload = {
        "qualification_score": qualification.get("score"),
        "qualification_label": qualification.get("label"),
        "qualification_reason": qualification.get("key_reason"),
        "personalization_points": qualification.get("personalization_points"),
        "status": "qualified" if qualification.get("label") == "qualified" else "new",
    }
    if enrichment:
        payload["enrichment_json"] = enrichment
        payload["enriched_at"] = datetime.utcnow().isoformat()
    db.table("leads").update(payload).eq("client_id", client_id).eq("email", email).execute()


def update_run_details(
    db: Client,
    run_id: str,
    status: str,
    steps: Optional[list[dict]] = None,
    llm_tokens_in: int = 0,
    llm_tokens_out: int = 0,
    cost_estimate_usd: float = 0.0,
    error_message: Optional[str] = None,
):
    payload = {
        "status": status,
        "llm_tokens_in": llm_tokens_in,
        "llm_tokens_out": llm_tokens_out,
        "cost_estimate_usd": cost_estimate_usd,
        "completed_at": datetime.utcnow().isoformat(),
        "steps_json": steps or [],
    }
    if error_message:
        payload["error_message"] = error_message
    db.table("runs").update(payload).eq("id", run_id).execute()
