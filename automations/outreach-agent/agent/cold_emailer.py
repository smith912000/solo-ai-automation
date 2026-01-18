import json
import logging
from dataclasses import dataclass
from typing import Optional

from .config import OUTREACH_MODEL, COLD_EMAIL_PROMPT

logger = logging.getLogger(__name__)


@dataclass
class ColdEmailDraft:
    subject: str
    body: str
    follow_up_task: Optional[str] = None
    tokens_in: int = 0
    tokens_out: int = 0
    model_name: Optional[str] = None
    raw_response: Optional[str] = None


def draft_cold_email(
    name: str,
    role: Optional[str],
    company: Optional[str],
    website: Optional[str],
    pain_points: Optional[str],
    notes: Optional[str] = None,
    llm_client=None,
) -> ColdEmailDraft:
    prompt = COLD_EMAIL_PROMPT.format(
        name=name or "there",
        role=role or "unknown",
        company=company or "your company",
        website=website or "n/a",
        pain_points=pain_points or "n/a",
        notes=notes or "n/a",
    )

    response, tokens_in, tokens_out = _call_llm(prompt, llm_client)
    draft = _parse_response(response)
    return ColdEmailDraft(
        subject=draft["email_subject"],
        body=draft["email_body"],
        follow_up_task=draft.get("follow_up_task"),
        tokens_in=tokens_in,
        tokens_out=tokens_out,
        model_name=OUTREACH_MODEL.name,
        raw_response=response,
    )


def _call_llm(prompt: str, client=None) -> tuple[str, int, int]:
    if client is None:
        from openai import OpenAI

        client = OpenAI()

    response = client.chat.completions.create(
        model=OUTREACH_MODEL.name,
        messages=[
            {"role": "system", "content": "Respond only with valid JSON."},
            {"role": "user", "content": prompt},
        ],
        max_tokens=OUTREACH_MODEL.max_tokens,
        temperature=OUTREACH_MODEL.temperature,
    )

    content = response.choices[0].message.content or ""
    tokens_in = response.usage.prompt_tokens if response.usage else 0
    tokens_out = response.usage.completion_tokens if response.usage else 0
    return content, tokens_in, tokens_out


def _parse_response(response: str) -> dict:
    clean_response = response.strip()
    if clean_response.startswith("```"):
        lines = clean_response.split("\n")
        clean_response = "\n".join(lines[1:-1])

    data = json.loads(clean_response)
    if "email_subject" not in data or "email_body" not in data:
        raise ValueError("Missing required email fields")

    logger.info("Drafted cold email")
    return data
