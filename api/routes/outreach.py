import importlib
import importlib.machinery
import importlib.util
import os
import sys
from typing import Optional

from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel

from lib.auth import require_auth

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
OUTREACH_ROOT = os.path.join(ROOT_DIR, "automations", "outreach-agent")
OUTREACH_AGENT_DIR = os.path.join(OUTREACH_ROOT, "agent")


def _load_agent_module(package_name: str, package_path: str, module_name: str):
    if package_name not in sys.modules:
        package = importlib.util.module_from_spec(
            importlib.machinery.ModuleSpec(package_name, None)
        )
        package.__path__ = [package_path]
        sys.modules[package_name] = package
    return importlib.import_module(f"{package_name}.{module_name}")


_outreach_module = _load_agent_module("outreach_agent", OUTREACH_AGENT_DIR, "cold_emailer")
draft_cold_email = _outreach_module.draft_cold_email


router = APIRouter(prefix="/outreach", tags=["outreach"])


class OutreachDraftRequest(BaseModel):
    name: str
    role: Optional[str] = None
    company: Optional[str] = None
    website: Optional[str] = None
    pain_points: Optional[str] = None
    notes: Optional[str] = None


@router.post("/draft")
def draft_outreach(
    payload: OutreachDraftRequest,
    x_api_key: Optional[str] = Header(default=None),
    x_password: Optional[str] = Header(default=None),
):
    require_auth(api_key=x_api_key, password=x_password)
    draft = draft_cold_email(
        name=payload.name,
        role=payload.role,
        company=payload.company,
        website=payload.website,
        pain_points=payload.pain_points,
        notes=payload.notes,
    )
    return {
        "email_subject": draft.subject,
        "email_body": draft.body,
        "follow_up_task": draft.follow_up_task,
        "tokens_in": draft.tokens_in,
        "tokens_out": draft.tokens_out,
        "model": draft.model_name,
    }
