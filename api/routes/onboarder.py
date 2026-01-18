import importlib
import importlib.machinery
import importlib.util
import os
import sys
from typing import Optional

from fastapi import APIRouter, Header
from pydantic import BaseModel, EmailStr

from lib.auth import require_auth

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
ONBOARDER_ROOT = os.path.join(ROOT_DIR, "automations", "client-onboarder")
ONBOARDER_AGENT_DIR = os.path.join(ONBOARDER_ROOT, "agent")


def _load_agent_module(package_name: str, package_path: str, module_name: str):
    if package_name not in sys.modules:
        package = importlib.util.module_from_spec(
            importlib.machinery.ModuleSpec(package_name, None)
        )
        package.__path__ = [package_path]
        sys.modules[package_name] = package
    return importlib.import_module(f"{package_name}.{module_name}")


_onboarder_module = _load_agent_module("client_onboarder_agent", ONBOARDER_AGENT_DIR, "main")
ClientInfo = _onboarder_module.ClientInfo
generate_checklist = _onboarder_module.generate_checklist


router = APIRouter(prefix="/onboarder", tags=["onboarder"])


class ChecklistRequest(BaseModel):
    client_name: str
    contact_name: str
    contact_email: EmailStr
    start_date: Optional[str] = None
    package: Optional[str] = None
    contract_signed: bool = False


@router.post("/checklist")
def create_checklist(
    payload: ChecklistRequest,
    x_api_key: Optional[str] = Header(default=None),
    x_password: Optional[str] = Header(default=None),
):
    require_auth(api_key=x_api_key, password=x_password, admin=True)
    info = ClientInfo(
        client_name=payload.client_name,
        contact_name=payload.contact_name,
        contact_email=payload.contact_email,
        start_date=payload.start_date,
        package=payload.package,
        contract_signed=payload.contract_signed,
    )
    return {"checklist": generate_checklist(info)}
