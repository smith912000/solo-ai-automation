import importlib
import importlib.machinery
import importlib.util
import os
import sys
from typing import Optional

from fastapi import APIRouter, Header
from pydantic import BaseModel

from lib.auth import require_auth
from lib import db as db_lib

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
create_session = _voice_module.create_session
handle_turn = _voice_module.handle_turn


router = APIRouter(prefix="/voice", tags=["voice"])


class VoiceCallRequest(BaseModel):
    phone_number: str
    script: str
    metadata: Optional[dict] = None


class VoiceSessionRequest(BaseModel):
    crm_lead_id: Optional[str] = None
    metadata: Optional[dict] = None


class VoiceTurnRequest(BaseModel):
    transcript: str
    context: Optional[dict] = None


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


@router.post("/sessions")
def create_voice_session(
    payload: VoiceSessionRequest,
    x_api_key: Optional[str] = Header(default=None),
    x_password: Optional[str] = Header(default=None),
):
    require_auth(api_key=x_api_key, password=x_password, admin=True)
    client_id = os.getenv("DEFAULT_CLIENT_ID")
    if not client_id:
        raise ValueError("DEFAULT_CLIENT_ID is not set")
    session = create_session(
        client_id=client_id,
        crm_lead_id=payload.crm_lead_id,
        metadata=payload.metadata,
    )
    return {"status": "ok", "session": session}


@router.post("/sessions/{session_id}/turn")
def create_voice_turn(
    session_id: str,
    payload: VoiceTurnRequest,
    x_api_key: Optional[str] = Header(default=None),
    x_password: Optional[str] = Header(default=None),
):
    require_auth(api_key=x_api_key, password=x_password, admin=True)
    result = handle_turn(session_id, payload.transcript, payload.context)
    return result


@router.get("/sessions/{session_id}")
def get_voice_session(
    session_id: str,
    x_api_key: Optional[str] = Header(default=None),
    x_password: Optional[str] = Header(default=None),
):
    require_auth(api_key=x_api_key, password=x_password, admin=True)
    db = db_lib.get_supabase_client()
    session = db_lib.get_voice_session(db, session_id)
    if not session:
        return {"status": "error", "error": "session_not_found"}
    turns = db_lib.list_voice_turns(db, session_id)
    return {"status": "ok", "session": session, "turns": turns}
