"""
Audit Module

Universal audit logging for all automations.
Every run produces a complete audit trail.
"""

import uuid
import json
import logging
from typing import Optional, Any
from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum

logger = logging.getLogger(__name__)


class RunStatus(Enum):
    """Possible run statuses."""
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    KILLED = "killed"
    SKIPPED = "skipped"
    REVERSED = "reversed"


@dataclass
class AuditStep:
    """A single step in the automation run."""
    step_name: str
    status: str  # started, completed, failed, skipped
    started_at: datetime = field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    duration_ms: Optional[int] = None
    input_summary: Optional[str] = None
    output_summary: Optional[str] = None
    error: Optional[str] = None
    tokens_used: int = 0
    metadata: dict = field(default_factory=dict)
    
    def complete(self, status: str = "completed", output: Optional[str] = None, error: Optional[str] = None):
        """Mark step as complete."""
        self.completed_at = datetime.utcnow()
        self.status = status
        self.duration_ms = int((self.completed_at - self.started_at).total_seconds() * 1000)
        if output:
            self.output_summary = output[:500]  # Truncate
        if error:
            self.error = error


@dataclass
class AutomationRunRecord:
    """
    Complete audit record for an automation run.
    
    This is the "audit primitive" - every automation must produce one.
    """
    # Identity
    run_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    automation_name: str = ""
    client_id: str = ""
    
    # Trigger
    trigger_type: str = "webhook"  # webhook, manual, scheduled
    trigger_source: Optional[str] = None
    idempotency_key: Optional[str] = None
    
    # Input
    input_data: dict = field(default_factory=dict)
    
    # Execution trace
    steps: list[AuditStep] = field(default_factory=list)
    decision_path: list[str] = field(default_factory=list)
    
    # Output
    output_data: dict = field(default_factory=dict)
    
    # Costs
    tokens_in: int = 0
    tokens_out: int = 0
    total_tokens: int = 0
    llm_model: Optional[str] = None
    cost_estimate_usd: float = 0.0
    
    # Status
    status: RunStatus = RunStatus.PENDING
    error_message: Optional[str] = None
    error_stack: Optional[str] = None
    
    # Kill switch
    killed_by: Optional[str] = None
    
    # Timing
    started_at: datetime = field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    duration_ms: Optional[int] = None
    
    # Reversal tracking
    reversal_reference: Optional[str] = None
    reversed_at: Optional[datetime] = None
    
    def start_step(self, step_name: str, input_summary: Optional[str] = None) -> AuditStep:
        """Start a new step and add to trace."""
        step = AuditStep(
            step_name=step_name,
            status="started",
            input_summary=input_summary[:500] if input_summary else None,
        )
        self.steps.append(step)
        self.decision_path.append(f"→ {step_name}")
        return step
    
    def add_decision(self, decision: str):
        """Add a decision point to the path."""
        self.decision_path.append(decision)
    
    def add_tokens(self, tokens_in: int = 0, tokens_out: int = 0):
        """Add token usage."""
        self.tokens_in += tokens_in
        self.tokens_out += tokens_out
        self.total_tokens = self.tokens_in + self.tokens_out
    
    def complete(
        self,
        status: RunStatus = RunStatus.SUCCESS,
        output: Optional[dict] = None,
        error: Optional[str] = None,
    ):
        """Mark run as complete."""
        self.completed_at = datetime.utcnow()
        self.status = status
        self.duration_ms = int((self.completed_at - self.started_at).total_seconds() * 1000)
        
        if output:
            self.output_data = output
        if error:
            self.error_message = error
        
        # Estimate cost (rough, based on GPT-4o pricing)
        self.cost_estimate_usd = (self.tokens_in * 0.000005) + (self.tokens_out * 0.000015)
    
    def kill(self, reason: str):
        """Mark run as killed."""
        self.status = RunStatus.KILLED
        self.killed_by = reason
        self.complete(status=RunStatus.KILLED, error=f"Killed: {reason}")
    
    def to_dict(self) -> dict:
        """Convert to dictionary for storage."""
        data = asdict(self)
        # Convert enums and datetimes
        data["status"] = self.status.value
        data["started_at"] = self.started_at.isoformat()
        if data["completed_at"]:
            data["completed_at"] = self.completed_at.isoformat()
        if data["reversed_at"]:
            data["reversed_at"] = self.reversed_at.isoformat()
        # Convert steps
        for step in data["steps"]:
            step["started_at"] = step["started_at"].isoformat() if step["started_at"] else None
            step["completed_at"] = step["completed_at"].isoformat() if step["completed_at"] else None
        return data
    
    def to_json(self) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict(), indent=2)


class AuditLogger:
    """
    Centralized audit logging.
    
    Handles persistence to database and optional real-time alerts.
    """
    
    def __init__(self, db_client=None, slack_webhook: Optional[str] = None):
        self.db_client = db_client
        self.slack_webhook = slack_webhook
        self._records: list[AutomationRunRecord] = []
    
    def create_run(
        self,
        automation_name: str,
        client_id: str,
        trigger_type: str = "webhook",
        idempotency_key: Optional[str] = None,
        input_data: Optional[dict] = None,
    ) -> AutomationRunRecord:
        """Create a new run record."""
        record = AutomationRunRecord(
            automation_name=automation_name,
            client_id=client_id,
            trigger_type=trigger_type,
            idempotency_key=idempotency_key,
            input_data=input_data or {},
        )
        self._records.append(record)
        return record
    
    def save(self, record: AutomationRunRecord):
        """Save run record to database."""
        if not self.db_client:
            logger.warning("No database client configured, skipping save")
            return
        
        try:
            data = record.to_dict()
            # Flatten for Supabase columns
            db_data = {
                "id": record.run_id,
                "client_id": record.client_id,
                "automation_name": record.automation_name,
                "trigger_type": record.trigger_type,
                "idempotency_key": record.idempotency_key,
                "trigger_payload": json.dumps(record.input_data),
                "steps_json": json.dumps(data["steps"]),
                "decision_path": " ".join(record.decision_path),
                "status": record.status.value,
                "error_message": record.error_message,
                "llm_tokens_in": record.tokens_in,
                "llm_tokens_out": record.tokens_out,
                "llm_model": record.llm_model,
                "cost_estimate_usd": record.cost_estimate_usd,
                "started_at": record.started_at.isoformat(),
                "completed_at": record.completed_at.isoformat() if record.completed_at else None,
                "duration_ms": record.duration_ms,
                "killed_by": record.killed_by,
            }
            
            self.db_client.table("runs").upsert(db_data).execute()
            logger.info(f"Saved run record: {record.run_id}")
            
        except Exception as e:
            logger.error(f"Failed to save run record: {e}")
    
    def alert_on_failure(self, record: AutomationRunRecord):
        """Send alert for failed runs."""
        if record.status in (RunStatus.FAILED, RunStatus.KILLED):
            self._send_alert(record)
    
    def _send_alert(self, record: AutomationRunRecord):
        """Send Slack alert."""
        if not self.slack_webhook:
            return
        
        try:
            import requests
            
            message = {
                "text": f"🚨 *Automation Failed*\n\n"
                        f"*Automation:* {record.automation_name}\n"
                        f"*Status:* {record.status.value}\n"
                        f"*Error:* {record.error_message}\n"
                        f"*Run ID:* {record.run_id}\n"
                        f"*Duration:* {record.duration_ms}ms"
            }
            
            requests.post(self.slack_webhook, json=message, timeout=5)
            
        except Exception as e:
            logger.error(f"Failed to send alert: {e}")
