import os
from dataclasses import dataclass
from typing import Optional

from lib import db as db_lib
from lib.training import build_sales_prompt


@dataclass
class CallResult:
    status: str
    call_id: Optional[str] = None
    summary: Optional[str] = None
    transcript: Optional[str] = None


def place_call(phone_number: str, script: str, metadata: Optional[dict] = None) -> CallResult:
    """
    Provider-agnostic call interface. Replace this with your voice API.
    """
    provider = os.getenv("VOICE_PROVIDER")
    if not provider:
        return CallResult(status="skipped", summary="VOICE_PROVIDER not configured")

    # Placeholder for external API integration.
    return CallResult(status="queued", call_id="voice-call-placeholder")


def create_session(
    client_id: str,
    crm_lead_id: Optional[str] = None,
    metadata: Optional[dict] = None,
) -> dict:
    db = db_lib.get_supabase_client()
    session = db_lib.create_voice_session(
        db,
        client_id=client_id,
        crm_lead_id=crm_lead_id,
        metadata=metadata,
        channel="web",
    )
    return session


def handle_turn(session_id: str, transcript: str, context: Optional[dict] = None) -> dict:
    db = db_lib.get_supabase_client()
    session = db_lib.get_voice_session(db, session_id)
    if not session:
        return {"status": "error", "error": "session_not_found"}

    db_lib.add_voice_turn(db, session_id, role="user", content=transcript)
    prompt = build_sales_prompt(
        role="voice_sales",
        product_summary=(context or {}).get("product_summary", "AI automation services"),
        lead_context=(context or {}).get("lead_context", transcript),
        desired_outcome=(context or {}).get("desired_outcome", "Schedule a short call"),
    )
    response_text = (
        "Thanks for sharing. I can give a quick overview and then we can decide "
        "if a short follow-up makes sense. What would be the best next step for you?"
    )
    db_lib.add_voice_turn(
        db,
        session_id,
        role="assistant",
        content=response_text,
        action="ask_next_step",
        confidence=0.75,
    )

    return {
        "status": "ok",
        "response": response_text,
        "action": "ask_next_step",
        "prompt": prompt,
    }


def run_demo():
    result = place_call(
        phone_number="+15555550100",
        script="Hi, this is Alex from Solo AI. Is now a bad time?",
        metadata={"lead": "demo"},
    )
    print(result)


if __name__ == "__main__":
    run_demo()
