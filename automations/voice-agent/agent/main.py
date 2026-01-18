import os
from dataclasses import dataclass
from typing import Optional


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


def run_demo():
    result = place_call(
        phone_number="+15555550100",
        script="Hi, this is Alex from Solo AI. Is now a bad time?",
        metadata={"lead": "demo"},
    )
    print(result)


if __name__ == "__main__":
    run_demo()
