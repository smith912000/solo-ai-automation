"""
Email sending utilities (SendGrid).
"""

import logging
import os
from typing import Optional

from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

logger = logging.getLogger(__name__)


def send_email(
    to_email: str,
    subject: str,
    body: str,
    from_email: Optional[str] = None,
    from_name: Optional[str] = None,
) -> dict:
    api_key = os.getenv("SENDGRID_API_KEY")
    if not api_key:
        raise ValueError("SENDGRID_API_KEY is not set")

    from_email = from_email or os.getenv("SENDGRID_FROM_EMAIL")
    from_name = from_name or os.getenv("SENDGRID_FROM_NAME") or ""
    if not from_email:
        raise ValueError("SENDGRID_FROM_EMAIL is not set")

    message = Mail(
        from_email=(from_email, from_name) if from_name else from_email,
        to_emails=to_email,
        subject=subject,
        plain_text_content=body,
    )

    client = SendGridAPIClient(api_key)
    try:
        response = client.send(message)
    except Exception as exc:
        logger.exception("SendGrid send failed")
        return {
            "status_code": None,
            "headers": {},
            "error": str(exc),
        }
    return {
        "status_code": response.status_code,
        "headers": dict(response.headers),
    }
