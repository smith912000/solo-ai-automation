"""
Outbox sender worker.
Sends approved emails and marks them as sent.
"""

import logging
import os
import time

from dotenv import load_dotenv

from lib import db as db_lib
from lib.email import send_email

logger = logging.getLogger(__name__)

load_dotenv()


def send_approved_once(limit: int = 10) -> int:
    db = db_lib.get_supabase_client()
    client_id = os.getenv("DEFAULT_CLIENT_ID")
    if not client_id:
        raise ValueError("DEFAULT_CLIENT_ID is not set")

    items = db_lib.list_outbox_approved(db, client_id, limit=limit)
    if not items:
        return 0

    sent = 0
    for record in items:
        response = send_email(
            record.get("to_email"),
            record.get("subject"),
            record.get("body"),
        )
        if response.get("error") or (response.get("status_code") or 0) >= 400:
            logger.error("SendGrid error for outbox %s: %s", record.get("id"), response)
            continue
        db_lib.mark_outbox_sent(db, record.get("id"), "sendgrid", response)
        db_lib.record_email_sent(
            db,
            client_id,
            record.get("lead_id"),
            record.get("to_email"),
            record.get("subject"),
        )
        db_lib.update_lead_status(
            db,
            client_id=client_id,
            lead_id=record.get("lead_id"),
            lead_email=record.get("to_email"),
            status="contacted",
        )
        sent += 1
    return sent


def run_loop():
    sleep_seconds = int(os.getenv("OUTBOX_POLL_SECONDS", "10"))
    batch_size = int(os.getenv("OUTBOX_BATCH_SIZE", "10"))
    while True:
        sent = send_approved_once(limit=batch_size)
        if sent == 0:
            time.sleep(sleep_seconds)


if __name__ == "__main__":
    run_loop()
