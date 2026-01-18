import os
from typing import Optional

from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel, EmailStr

from worker.main import process_payload
from lib.auth import require_api_key


router = APIRouter(prefix="/qualify", tags=["internal"])


class ManualQualifyRequest(BaseModel):
    name: str
    email: EmailStr
    company: Optional[str] = None
    website: Optional[str] = None
    message: Optional[str] = None
    source: Optional[str] = None
    timestamp: Optional[str] = None


@router.post("")
def manual_qualify(
    payload: ManualQualifyRequest,
    x_client_id: Optional[str] = Header(default=None),
    x_api_key: Optional[str] = Header(default=None),
):
    require_api_key(x_api_key)
    client_id = x_client_id or os.getenv("DEFAULT_CLIENT_ID")
    if not client_id:
        raise HTTPException(status_code=500, detail="DEFAULT_CLIENT_ID is not set")

    result = process_payload(
        client_id=client_id,
        payload=payload.dict(),
        run_id=None,
        idempotency_key=None,
        approval_mode_override=True,
    )
    return result
