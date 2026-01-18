"""
Worker process for jobs_queue.
Only component that calls enrichment + LLM + email.
"""

import logging
import os
import sys
import time
from typing import Optional

from dotenv import load_dotenv

from lib import db as db_lib
from lib.cost_tracker import get_cost_tracker
from lib.enrichment import enrich_company
from lib.email import send_email
from lib.kill_switch import create_default_kill_switch, KillSwitchTriggered
from lib.slack import send_slack_alert

logger = logging.getLogger(__name__)

load_dotenv()

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
AGENT_ROOT = os.path.join(ROOT_DIR, "automations", "lead-qualifier")
if AGENT_ROOT not in sys.path:
    sys.path.append(AGENT_ROOT)

from agent.qualifier import qualify_lead  # noqa: E402
from agent.email_drafter import draft_email  # noqa: E402
from agent.config import EMAIL_COOLDOWN_DAYS, APPROVAL_MODE  # noqa: E402


def send_approved_emails(limit: int = 10) -> int:
    db = db_lib.get_supabase_client()
    client_id = os.getenv("DEFAULT_CLIENT_ID")
    if not client_id:
        raise ValueError("DEFAULT_CLIENT_ID is not set")

    items = db_lib.list_outbox_approved(db, client_id, limit=limit)
    if not items:
        return 0

    sent = 0
    for record in items:
        response = send_email(
            record.get("to_email"),
            record.get("subject"),
            record.get("body"),
        )
        if response.get("error") or (response.get("status_code") or 0) >= 400:
            logger.error("SendGrid error for outbox %s: %s", record.get("id"), response)
            continue
        db_lib.mark_outbox_sent(db, record.get("id"), "sendgrid", response)
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
        sent += 1
    return sent


def process_payload(
    client_id: str,
    payload: dict,
    run_id: Optional[str],
    idempotency_key: Optional[str],
    approval_mode_override: Optional[bool] = None,
) -> dict:
    db = db_lib.get_supabase_client()
    tracker = get_cost_tracker()
    kill_switch = create_default_kill_switch()
    if os.getenv("SLACK_WEBHOOK_URL"):
        def _alert_kill_switch(reason: str) -> None:
            send_slack_alert(
                "Kill switch triggered for lead-qualifier.",
                level="critical",
                context={
                    "client_id": client_id,
                    "run_id": run_id,
                    "reason": reason,
                },
            )

        kill_switch.add_alert_callback(_alert_kill_switch)
    max_cost_per_run = float(os.getenv("MAX_COST_PER_RUN_USD", "0.50"))
    steps: list[dict] = []
    tokens_in_total = 0
    tokens_out_total = 0
    cost_total = 0.0

    email = db_lib.normalize_email(payload.get("email", ""))
    name = payload.get("name")
    company = payload.get("company")
    website = payload.get("website")
    message = payload.get("message")
    source = payload.get("source")

    steps.append({"step": "input", "status": "ok"})

    # Upsert lead
    db_lib.upsert_lead(
        db,
        client_id=client_id,
        lead={
            "email": email,
            "name": name,
            "company": company,
            "website": website,
            "message": message,
            "source": source,
        },
    )
    steps.append({"step": "lead_upsert", "status": "ok"})

    automation_status = db_lib.get_automation_status(db, client_id, "lead-qualifier")
    if automation_status.get("status") == "paused":
        steps.append({"step": "automation_status", "status": "paused"})
        if run_id:
            db_lib.update_run_details(
                db,
                run_id=run_id,
                status="skipped",
                steps=steps,
                llm_tokens_in=tokens_in_total,
                llm_tokens_out=tokens_out_total,
                cost_estimate_usd=cost_total,
                error_message="automation_paused",
            )
        return {"status": "skipped", "reason": "automation_paused"}

    # Suppression list
    if db_lib.is_email_suppressed(db, client_id, email):
        if run_id:
            db_lib.update_run_details(
                db,
                run_id=run_id,
                status="skipped",
                steps=steps,
                llm_tokens_in=tokens_in_total,
                llm_tokens_out=tokens_out_total,
                cost_estimate_usd=cost_total,
                error_message="suppressed",
            )
        return {"status": "skipped", "reason": "suppressed"}

    # Do-not-contact window
    if db_lib.email_sent_recently(db, client_id, email, EMAIL_COOLDOWN_DAYS):
        if run_id:
            db_lib.update_run_details(
                db,
                run_id=run_id,
                status="skipped",
                steps=steps,
                llm_tokens_in=tokens_in_total,
                llm_tokens_out=tokens_out_total,
                cost_estimate_usd=cost_total,
                error_message="cooldown",
            )
        return {"status": "skipped", "reason": "cooldown"}

    try:
        # Enrichment
        enrichment = enrich_company(website)
        steps.append({"step": "enrichment", "status": "ok"})

        # Qualification
        qualification = qualify_lead(
            name=name,
            email=email,
            company=company,
            website=website,
            message=message,
            source=source,
            enrichment_data=enrichment,
        )
        tokens_in_total += qualification.tokens_in
        tokens_out_total += qualification.tokens_out
        kill_switch.add_tokens(qualification.tokens_used)
        if qualification.model_name:
            cost_total += tracker.record_usage(
                automation="lead-qualifier",
                client_id=client_id,
                model=qualification.model_name,
                tokens_in=qualification.tokens_in,
                tokens_out=qualification.tokens_out,
                run_id=run_id,
            )
        if cost_total > max_cost_per_run:
            raise KillSwitchTriggered(
                f"cost_limit_exceeded (${cost_total:.2f} > ${max_cost_per_run:.2f})"
            )
        if kill_switch.should_kill():
            raise KillSwitchTriggered(kill_switch.state.kill_reason or "kill_switch")
    except KillSwitchTriggered as exc:
        if not kill_switch.state.is_killed:
            send_slack_alert(
                "Kill switch triggered for lead-qualifier.",
                level="critical",
                context={
                    "client_id": client_id,
                    "run_id": run_id,
                    "reason": str(exc),
                },
            )
        if run_id:
            db_lib.update_run_details(
                db,
                run_id=run_id,
                status="killed",
                steps=steps,
                llm_tokens_in=tokens_in_total,
                llm_tokens_out=tokens_out_total,
                cost_estimate_usd=cost_total,
                error_message=str(exc),
            )
        return {"status": "killed", "reason": str(exc)}
    steps.append(
        {
            "step": "qualification",
            "status": "ok",
            "label": qualification.label,
            "score": qualification.score,
            "tokens": qualification.tokens_used,
        }
    )

    if qualification.score >= 80:
        send_slack_alert(
            "High-score lead qualified.",
            level="info",
            context={
                "client_id": client_id,
                "run_id": run_id,
                "lead_name": name,
                "lead_email": email,
                "company": company,
                "score": qualification.score,
            },
        )

    # Disqualified -> log and exit
    if qualification.label == "disqualified":
        if run_id:
            db_lib.update_run_details(
                db,
                run_id=run_id,
                status="success",
                steps=steps,
                llm_tokens_in=tokens_in_total,
                llm_tokens_out=tokens_out_total,
                cost_estimate_usd=cost_total,
            )
        db_lib.update_lead_qualification(
            db,
            client_id=client_id,
            email=email,
            qualification={
                "score": qualification.score,
                "label": qualification.label,
                "key_reason": qualification.key_reason,
                "personalization_points": qualification.personalization_points,
            },
            enrichment=enrichment,
        )
        return {"status": "disqualified"}

    try:
        # Draft email
        draft = draft_email(
            name=name,
            company=company,
            message=message,
            qualification=qualification,
            enrichment_data=enrichment,
        )
        tokens_in_total += draft.tokens_in
        tokens_out_total += draft.tokens_out
        kill_switch.add_tokens(draft.tokens_used)
        if draft.model_name:
            cost_total += tracker.record_usage(
                automation="lead-qualifier",
                client_id=client_id,
                model=draft.model_name,
                tokens_in=draft.tokens_in,
                tokens_out=draft.tokens_out,
                run_id=run_id,
            )
        if cost_total > max_cost_per_run:
            raise KillSwitchTriggered(
                f"cost_limit_exceeded (${cost_total:.2f} > ${max_cost_per_run:.2f})"
            )
        if kill_switch.should_kill():
            raise KillSwitchTriggered(kill_switch.state.kill_reason or "kill_switch")
    except KillSwitchTriggered as exc:
        if not kill_switch.state.is_killed:
            send_slack_alert(
                "Kill switch triggered for lead-qualifier.",
                level="critical",
                context={
                    "client_id": client_id,
                    "run_id": run_id,
                    "reason": str(exc),
                },
            )
        if run_id:
            db_lib.update_run_details(
                db,
                run_id=run_id,
                status="killed",
                steps=steps,
                llm_tokens_in=tokens_in_total,
                llm_tokens_out=tokens_out_total,
                cost_estimate_usd=cost_total,
                error_message=str(exc),
            )
        return {"status": "killed", "reason": str(exc)}
    steps.append({"step": "email_draft", "status": "ok", "tokens": draft.tokens_used})

    # Send or queue
    approval_mode = approval_mode_override if approval_mode_override is not None else APPROVAL_MODE
    email_status = "queued"
    if qualification.label == "review" or approval_mode:
        db_lib.queue_email(
            db,
            client_id=client_id,
            lead_id=None,
            run_id=run_id,
            to_email=email,
            to_name=name or "",
            subject=draft.subject,
            body=draft.body,
        )
        email_status = "queued"
    else:
        response = send_email(email, draft.subject, draft.body)
        if response.get("error") or (response.get("status_code") or 0) >= 400:
            raise RuntimeError(f"SendGrid send failed: {response}")
        db_lib.record_email_sent(db, client_id, None, email, draft.subject)
        email_status = "sent"

    steps.append({"step": "email_send", "status": email_status})

    db_lib.update_lead_qualification(
        db,
        client_id=client_id,
        email=email,
        qualification={
            "score": qualification.score,
            "label": qualification.label,
            "key_reason": qualification.key_reason,
            "personalization_points": qualification.personalization_points,
        },
        enrichment=enrichment,
    )

    if run_id:
        db_lib.update_run_details(
            db,
            run_id=run_id,
            status="success",
            steps=steps,
            llm_tokens_in=tokens_in_total,
            llm_tokens_out=tokens_out_total,
            cost_estimate_usd=cost_total,
        )

    return {
        "status": "success",
        "email_status": email_status,
        "qualification_label": qualification.label,
    }


def process_job(job: dict) -> dict:
    payload = job.get("payload") or {}
    client_id = job.get("client_id")
    run_id = payload.get("run_id")
    idempotency_key = payload.get("idempotency_key")
    return process_payload(client_id, payload, run_id, idempotency_key)


def run_once():
    db = db_lib.get_supabase_client()
    worker_id = os.getenv("WORKER_ID", "worker-1")
    lease_seconds = int(os.getenv("QUEUE_LEASE_SECONDS", "120"))
    max_attempts = int(os.getenv("QUEUE_MAX_ATTEMPTS", "5"))

    job = db_lib.claim_next_job(db, worker_id, lease_seconds)
    if not job:
        return False

    job_id = job.get("id")
    attempts = job.get("attempts", 0)
    run_id = (job.get("payload") or {}).get("run_id")

    try:
        process_job(job)
        db_lib.mark_job_done(db, job_id, "done")
    except Exception as exc:
        if attempts >= max_attempts:
            db_lib.mark_job_done(db, job_id, "dead", error_message=str(exc))
            if run_id:
                db_lib.update_run_status(db, run_id, "failed", error_message=str(exc))
            send_slack_alert(
                "Worker job failed and marked dead.",
                level="error",
                context={
                    "job_id": job_id,
                    "run_id": run_id,
                    "attempts": attempts,
                    "error": str(exc),
                },
            )
        else:
            db_lib.requeue_job(db, job_id, delay_seconds=30, error_message=str(exc))
            send_slack_alert(
                "Worker job failed and was requeued.",
                level="warning",
                context={
                    "job_id": job_id,
                    "run_id": run_id,
                    "attempts": attempts,
                    "error": str(exc),
                },
            )
    return True


def run_loop():
    sleep_seconds = int(os.getenv("WORKER_POLL_SECONDS", "2"))
    outbox_enabled = os.getenv("OUTBOX_SEND_ENABLED", "").lower() in {"1", "true", "yes"}
    outbox_batch = int(os.getenv("OUTBOX_BATCH_SIZE", "10"))
    while True:
        ran = run_once()
        if outbox_enabled:
            send_approved_emails(limit=outbox_batch)
        if not ran:
            time.sleep(sleep_seconds)


if __name__ == "__main__":
    run_loop()
