import os
import logging
from dataclasses import dataclass
from typing import Optional

import requests

from lib import db as db_lib
from lib.training import build_sales_prompt
from .scripts import build_call_script

logger = logging.getLogger(__name__)


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

    metadata = metadata or {}
    script = script or build_call_script(metadata.get("name"), metadata.get("company"))

    client_id = metadata.get("client_id")
    session_id = None
    if client_id:
        session = create_session(client_id=client_id, crm_lead_id=metadata.get("lead_id"), metadata=metadata)
        session_id = session.get("id")

    api_url = None
    api_key = None
    provider = provider.lower()
    if provider == "vapi":
        api_url = os.getenv("VAPI_API_URL")
        api_key = os.getenv("VAPI_API_KEY")
    elif provider == "bland":
        api_url = os.getenv("BLAND_API_URL")
        api_key = os.getenv("BLAND_API_KEY")
    else:
        api_url = os.getenv("VOICE_API_URL")
        api_key = os.getenv("VOICE_API_KEY")
    if not api_url or not api_key:
        return CallResult(status="error", summary="Voice provider API not configured")

    if session_id:
        metadata["session_id"] = session_id

    # Build provider-specific payload
    if provider == "vapi":
        # Vapi expects: phoneNumberId, customer.number, and assistant config
        payload = {
            "customer": {
                "number": phone_number,
            },
            "assistant": {
                "firstMessage": script,
                "model": {
                    "provider": "openai",
                    "model": "gpt-4o-mini",
                    "messages": [
                        {
                            "role": "system",
                            "content": script
                        }
                    ]
                },
                "voice": {
                    "provider": "11labs",
                    "voiceId": "21m00Tcm4TlvDq8ikWAM"  # Rachel voice
                }
            },
            "metadata": metadata,
        }
    else:
        payload = {
            "to": phone_number,
            "script": script,
            "metadata": metadata,
            "provider": provider,
        }

    try:
        response = requests.post(
            api_url,
            json=payload,
            headers={"Authorization": f"Bearer {api_key}"},
            timeout=10,
        )
        response.raise_for_status()
        data = response.json() if response.content else {}
        call_id = data.get("call_id") or data.get("id") or "voice-call"
        if session_id:
            db_lib.add_voice_turn(
                db_lib.get_supabase_client(),
                session_id,
                role="system",
                content=f"Call queued via {provider}",
                action="call_queued",
                confidence=1.0,
            )
        return CallResult(status="queued", call_id=call_id, summary="Call queued")
    except Exception as exc:
        logger.error("Voice provider call failed: %s", exc)
        if session_id:
            db_lib.add_voice_turn(
                db_lib.get_supabase_client(),
                session_id,
                role="system",
                content=f"Call failed: {exc}",
                action="call_failed",
                confidence=0.2,
            )
        return CallResult(status="error", summary=str(exc))


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
