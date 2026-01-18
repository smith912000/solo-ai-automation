"""
Slack alerting utilities.
"""

from __future__ import annotations

import logging
import os
from typing import Optional

import requests

logger = logging.getLogger(__name__)


LEVEL_PREFIX = {
    "info": "[INFO]",
    "warning": "[WARN]",
    "error": "[ERROR]",
    "critical": "[CRITICAL]",
}


def _format_context(context: Optional[dict]) -> str:
    if not context:
        return ""
    lines = []
    for key, value in context.items():
        if value is None:
            continue
        lines.append(f"*{key}:* {value}")
    return "\n" + "\n".join(lines) if lines else ""


def send_slack_alert(message: str, level: str = "info", context: Optional[dict] = None) -> bool:
    webhook = os.getenv("SLACK_WEBHOOK_URL")
    if not webhook:
        logger.info("Slack webhook not configured; skipping alert")
        return False

    normalized_level = (level or "info").lower()
    prefix = LEVEL_PREFIX.get(normalized_level, "[INFO]")
    text = f"{prefix} *{normalized_level.upper()}*\n{message}{_format_context(context)}"

    try:
        response = requests.post(webhook, json={"text": text}, timeout=5)
        response.raise_for_status()
        return True
    except Exception as exc:
        logger.error("Failed to send Slack alert: %s", exc)
        return False
