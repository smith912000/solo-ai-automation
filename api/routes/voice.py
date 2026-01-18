import importlib
import importlib.machinery
import importlib.util
import os
import sys
from typing import Optional

from fastapi import APIRouter, Header
from pydantic import BaseModel

from lib.auth import require_auth

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
VOICE_ROOT = os.path.join(ROOT_DIR, "automations", "voice-agent")
VOICE_AGENT_DIR = os.path.join(VOICE_ROOT, "agent")


def _load_agent_module(package_name: str, package_path: str, module_name: str):
    if package_name not in sys.modules:
        package = importlib.util.module_from_spec(
            importlib.machinery.ModuleSpec(package_name, None)
        )
        package.__path__ = [package_path]
        sys.modules[package_name] = package
    return importlib.import_module(f"{package_name}.{module_name}")


_voice_module = _load_agent_module("voice_agent", VOICE_AGENT_DIR, "main")
place_call = _voice_module.place_call


router = APIRouter(prefix="/voice", tags=["voice"])


class VoiceCallRequest(BaseModel):
    phone_number: str
    script: str
    metadata: Optional[dict] = None


@router.post("/call")
def place_voice_call(
    payload: VoiceCallRequest,
    x_api_key: Optional[str] = Header(default=None),
    x_password: Optional[str] = Header(default=None),
):
    require_auth(api_key=x_api_key, password=x_password, admin=True)
    result = place_call(payload.phone_number, payload.script, payload.metadata)
    return {
        "status": result.status,
        "call_id": result.call_id,
        "summary": result.summary,
        "transcript": result.transcript,
    }
