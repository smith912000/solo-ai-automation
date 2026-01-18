from fastapi import APIRouter

from lib import db as db_lib


router = APIRouter(tags=["status"])


@router.get("/health")
def health():
    return {"status": "ok"}


@router.get("/status")
def status():
    db = db_lib.get_supabase_client()
    queue_counts = db_lib.get_queue_counts(db)
    return {
        "queue": queue_counts,
    }
