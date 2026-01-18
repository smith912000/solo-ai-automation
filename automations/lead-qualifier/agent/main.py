"""
Lead Qualifier Agent - Main Entry Point

This is the primary interface called by n8n or other orchestrators.
Includes kill switches, audit logging, and graceful error handling.
"""

import os
import time
import json
import hashlib
import logging
from datetime import datetime, timedelta
from typing import Optional
from dataclasses import dataclass, asdict

from .config import (
    MAX_TOKENS_PER_RUN,
    MAX_EXECUTION_TIME_SECONDS,
    EMAIL_COOLDOWN_DAYS,
    APPROVAL_MODE,
)
from .qualifier import qualify_lead, QualificationResult
from .email_drafter import draft_email, EmailDraft

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class RunResult:
    """Complete result of a lead qualification run."""
    run_id: str
    status: str  # success, failed, killed, skipped
    lead_email: str
    
    # Qualification
    qualification: Optional[dict] = None
    
    # Email
    email_draft: Optional[dict] = None
    email_status: str = "none"  # none, queued, sent, skipped
    
    # Costs
    total_tokens: int = 0
    estimated_cost_usd: float = 0.0
    
    # Timing
    duration_ms: int = 0
    
    # Errors
    error: Optional[str] = None
    killed_by: Optional[str] = None
    
    # Audit trail
    steps: list = None
    
    def __post_init__(self):
        if self.steps is None:
            self.steps = []


def process_lead(
    name: str,
    email: str,
    company: Optional[str] = None,
    website: Optional[str] = None,
    message: Optional[str] = None,
    source: Optional[str] = None,
    timestamp: Optional[str] = None,
    client_id: str = "default",
    enrichment_data: Optional[dict] = None,
    offer_description: Optional[str] = None,
    db_client = None,  # Supabase client
    llm_client = None,  # OpenAI client
) -> RunResult:
    """
    Main entry point for lead qualification.
    
    This function:
    1. Checks idempotency (no duplicate processing)
    2. Checks email cooldown (no spam)
    3. Qualifies the lead
    4. Drafts email if qualified
    5. Queues or sends email based on APPROVAL_MODE
    6. Logs everything for audit
    
    Args:
        name: Contact name
        email: Contact email (required)
        company: Company name
        website: Company website
        message: Form message
        source: Lead source
        timestamp: ISO timestamp of form submit
        client_id: Client identifier for multi-tenant isolation
        enrichment_data: Pre-fetched enrichment data
        offer_description: Custom offer description
        db_client: Supabase client for database operations
        llm_client: OpenAI client for LLM calls
    
    Returns:
        RunResult with complete audit trail
    """
    
    start_time = time.time()
    run_id = _generate_run_id()
    
    result = RunResult(
        run_id=run_id,
        status="pending",
        lead_email=email,
    )
    
    try:
        # =========================================================
        # STEP 1: Idempotency Check
        # =========================================================
        idempotency_key = _compute_idempotency_key(email, timestamp, source)
        result.steps.append({"step": "idempotency_check", "key": idempotency_key})
        
        if db_client and _run_exists(db_client, idempotency_key):
            result.status = "skipped"
            result.killed_by = "idempotency"
            result.steps.append({"step": "skipped", "reason": "duplicate_run"})
            logger.info(f"Skipping duplicate run: {idempotency_key}")
            return _finalize_result(result, start_time)
        
        # =========================================================
        # STEP 2: Email Cooldown Check
        # =========================================================
        result.steps.append({"step": "cooldown_check"})
        
        if db_client and _email_sent_recently(db_client, client_id, email, EMAIL_COOLDOWN_DAYS):
            result.status = "skipped"
            result.killed_by = "email_cooldown"
            result.email_status = "skipped"
            result.steps.append({
                "step": "skipped",
                "reason": f"email_sent_within_{EMAIL_COOLDOWN_DAYS}_days"
            })
            logger.info(f"Skipping {email}: recently contacted")
            return _finalize_result(result, start_time)
        
        # =========================================================
        # STEP 3: Qualify Lead
        # =========================================================
        result.steps.append({"step": "qualification", "status": "started"})
        
        _check_kill_conditions(result, start_time)  # Kill switch check
        
        qualification = qualify_lead(
            name=name,
            email=email,
            company=company,
            website=website,
            message=message,
            source=source,
            enrichment_data=enrichment_data,
            offer_description=offer_description,
            llm_client=llm_client,
        )
        
        result.qualification = {
            "score": qualification.score,
            "label": qualification.label,
            "key_reason": qualification.key_reason,
            "personalization_points": qualification.personalization_points,
        }
        result.total_tokens += qualification.tokens_used
        result.steps.append({
            "step": "qualification",
            "status": "completed",
            "score": qualification.score,
            "label": qualification.label,
            "tokens": qualification.tokens_used,
        })
        
        logger.info(f"Qualified {email}: {qualification.label} ({qualification.score})")
        
        # =========================================================
        # STEP 4: Check if we should draft email
        # =========================================================
        if qualification.label == "disqualified":
            result.status = "success"
            result.email_status = "skipped"
            result.steps.append({"step": "email", "status": "skipped", "reason": "disqualified"})
            return _finalize_result(result, start_time)
        
        # =========================================================
        # STEP 5: Draft Email
        # =========================================================
        _check_kill_conditions(result, start_time)  # Kill switch check
        
        result.steps.append({"step": "email_draft", "status": "started"})
        
        email_draft = draft_email(
            name=name,
            company=company,
            message=message,
            qualification=qualification,
            enrichment_data=enrichment_data,
            offer_description=offer_description,
            llm_client=llm_client,
        )
        
        result.email_draft = {
            "subject": email_draft.subject,
            "body": email_draft.body,
            "follow_up_task": email_draft.follow_up_task,
        }
        result.total_tokens += email_draft.tokens_used
        result.steps.append({
            "step": "email_draft",
            "status": "completed",
            "tokens": email_draft.tokens_used,
        })
        
        # =========================================================
        # STEP 6: Send or Queue Email
        # =========================================================
        _check_kill_conditions(result, start_time)  # Kill switch check
        
        if qualification.label == "review":
            # Always queue for review
            result.email_status = "queued_for_review"
            result.steps.append({"step": "email_send", "status": "queued", "reason": "needs_review"})
            
            if db_client:
                _queue_email(db_client, client_id, email, name, email_draft, run_id)
                
        elif APPROVAL_MODE:
            # Queue for approval
            result.email_status = "queued_for_approval"
            result.steps.append({"step": "email_send", "status": "queued", "reason": "approval_mode"})
            
            if db_client:
                _queue_email(db_client, client_id, email, name, email_draft, run_id)
                
        else:
            # Auto-send (only if approval mode is off)
            result.email_status = "sent"
            result.steps.append({"step": "email_send", "status": "sent"})
            
            # TODO: Implement actual email sending via SendGrid
            # send_email(email, email_draft.subject, email_draft.body)
            
            if db_client:
                _record_email_sent(db_client, client_id, email, email_draft.subject)
        
        result.status = "success"
        return _finalize_result(result, start_time)
        
    except KillSwitchTriggered as e:
        result.status = "killed"
        result.killed_by = str(e)
        result.error = f"Kill switch: {e}"
        result.steps.append({"step": "killed", "reason": str(e)})
        logger.warning(f"Run killed: {e}")
        return _finalize_result(result, start_time)
        
    except Exception as e:
        result.status = "failed"
        result.error = str(e)
        result.steps.append({"step": "error", "message": str(e)})
        logger.error(f"Run failed: {e}", exc_info=True)
        return _finalize_result(result, start_time)


class KillSwitchTriggered(Exception):
    """Raised when a kill condition is met."""
    pass


def _check_kill_conditions(result: RunResult, start_time: float):
    """Check all kill conditions and raise if any are met."""
    
    # Token limit
    if result.total_tokens > MAX_TOKENS_PER_RUN:
        raise KillSwitchTriggered(f"token_limit_exceeded ({result.total_tokens} > {MAX_TOKENS_PER_RUN})")
    
    # Time limit
    elapsed = time.time() - start_time
    if elapsed > MAX_EXECUTION_TIME_SECONDS:
        raise KillSwitchTriggered(f"timeout ({elapsed:.0f}s > {MAX_EXECUTION_TIME_SECONDS}s)")


def _generate_run_id() -> str:
    """Generate a unique run ID."""
    import uuid
    return str(uuid.uuid4())


def _compute_idempotency_key(email: str, timestamp: Optional[str], source: Optional[str]) -> str:
    """Compute idempotency key from inputs."""
    key_input = f"{email}:{timestamp or ''}:{source or ''}"
    return hashlib.sha256(key_input.encode()).hexdigest()[:32]


def _finalize_result(result: RunResult, start_time: float) -> RunResult:
    """Add final timing and cost estimates."""
    result.duration_ms = int((time.time() - start_time) * 1000)
    
    # Rough cost estimate (GPT-4o pricing)
    # $5/1M input, $15/1M output, assume 50/50 split
    result.estimated_cost_usd = result.total_tokens * 0.00001  # ~$10/1M average
    
    return result


# =============================================================================
# Database Operations (Supabase)
# =============================================================================
# These are stubs - implement with actual Supabase client

def _run_exists(db_client, idempotency_key: str) -> bool:
    """Check if a run with this idempotency key already exists."""
    try:
        response = db_client.table("runs").select("id").eq("idempotency_key", idempotency_key).execute()
        return len(response.data) > 0
    except Exception as e:
        logger.warning(f"Failed to check idempotency: {e}")
        return False  # Fail open - allow the run


def _email_sent_recently(db_client, client_id: str, email: str, days: int) -> bool:
    """Check if we've emailed this lead recently."""
    try:
        cutoff = (datetime.utcnow() - timedelta(days=days)).isoformat()
        response = (
            db_client.table("email_history")
            .select("id")
            .eq("client_id", client_id)
            .eq("lead_email", email)
            .gte("sent_at", cutoff)
            .execute()
        )
        return len(response.data) > 0
    except Exception as e:
        logger.warning(f"Failed to check email history: {e}")
        return False  # Fail open


def _queue_email(db_client, client_id: str, to_email: str, to_name: str, draft: EmailDraft, run_id: str):
    """Insert email into approval queue."""
    try:
        db_client.table("outbox_emails").insert({
            "client_id": client_id,
            "run_id": run_id,
            "to_email": to_email,
            "to_name": to_name,
            "subject": draft.subject,
            "body": draft.body,
            "status": "queued",
        }).execute()
    except Exception as e:
        logger.error(f"Failed to queue email: {e}")


def _record_email_sent(db_client, client_id: str, email: str, subject: str):
    """Record that an email was sent."""
    try:
        db_client.table("email_history").insert({
            "client_id": client_id,
            "lead_email": email,
            "subject": subject,
            "sent_at": datetime.utcnow().isoformat(),
        }).execute()
    except Exception as e:
        logger.error(f"Failed to record email: {e}")


# =============================================================================
# CLI Entry Point (for testing)
# =============================================================================

if __name__ == "__main__":
    import sys
    
    # Simple test
    result = process_lead(
        name="Test User",
        email="test@example.com",
        company="Acme Corp",
        message="I'm interested in AI automation for my sales team",
        source="website",
    )
    
    print(json.dumps(asdict(result), indent=2))
    sys.exit(0 if result.status == "success" else 1)
