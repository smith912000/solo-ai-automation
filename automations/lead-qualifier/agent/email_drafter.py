"""
Lead Qualifier - Email Drafting Logic

This module handles personalized email generation for qualified leads.
"""

import json
import logging
from typing import Optional
from dataclasses import dataclass

from .config import (
    DRAFTING_MODEL,
    EMAIL_DRAFT_PROMPT,
    DEFAULT_OFFER,
    MAX_RETRIES_PER_STEP,
)
from .qualifier import QualificationResult

logger = logging.getLogger(__name__)


@dataclass
class EmailDraft:
    """Structured result from email drafting."""
    subject: str
    body: str
    follow_up_task: Optional[str] = None
    tokens_used: int = 0
    tokens_in: int = 0
    tokens_out: int = 0
    model_name: Optional[str] = None
    raw_response: Optional[str] = None


def draft_email(
    name: str,
    company: Optional[str],
    message: Optional[str],
    qualification: QualificationResult,
    enrichment_data: Optional[dict] = None,
    offer_description: Optional[str] = None,
    llm_client = None,
) -> EmailDraft:
    """
    Draft a personalized email for a qualified lead.
    
    Args:
        name: Contact name
        company: Company name
        message: Original form message
        qualification: QualificationResult from qualifier
        enrichment_data: Dict of enrichment info
        offer_description: Custom offer description
        llm_client: OpenAI client instance
    
    Returns:
        EmailDraft with subject, body, and follow-up task
    
    Raises:
        ValueError: If LLM returns invalid response after retries
    """
    
    # Format personalization points
    points_formatted = "\n".join(
        f"- {point}" for point in qualification.personalization_points
    ) or "- General interest in automation"
    
    # Build prompt
    prompt = EMAIL_DRAFT_PROMPT.format(
        offer_description=offer_description or DEFAULT_OFFER,
        name=name or "there",
        company=company or "your company",
        message=message or "(No message provided)",
        score=qualification.score,
        key_reason=qualification.key_reason,
        personalization_points=points_formatted,
        enrichment_data=_format_enrichment(enrichment_data),
    )
    
    # Call LLM with retries
    last_error = None
    for attempt in range(MAX_RETRIES_PER_STEP + 1):
        try:
            response, tokens_in, tokens_out = _call_llm(prompt, llm_client)
            draft = _parse_email_response(response, tokens_in, tokens_out)
            
            # Post-process: ensure name is in email
            draft = _personalize_draft(draft, name)
            
            logger.info(f"Email drafted: subject='{draft.subject[:50]}...'")
            return draft
            
        except (json.JSONDecodeError, KeyError, ValueError) as e:
            last_error = e
            logger.warning(f"Email draft attempt {attempt + 1} failed: {e}")
            
            if attempt < MAX_RETRIES_PER_STEP:
                prompt += "\n\nIMPORTANT: Your previous response was not valid JSON. Respond ONLY with the JSON object."
    
    # All retries failed
    raise ValueError(f"Failed to draft email after {MAX_RETRIES_PER_STEP + 1} attempts: {last_error}")


def _call_llm(prompt: str, client = None) -> tuple[str, int, int]:
    """Call the LLM and return response + token count."""
    if client is None:
        from openai import OpenAI
        client = OpenAI()
    
    response = client.chat.completions.create(
        model=DRAFTING_MODEL.name,
        messages=[
            {"role": "system", "content": "You are an expert at writing personalized, engaging outreach emails. Respond only with valid JSON."},
            {"role": "user", "content": prompt}
        ],
        max_tokens=DRAFTING_MODEL.max_tokens,
        temperature=DRAFTING_MODEL.temperature,
    )
    
    content = response.choices[0].message.content or ""
    tokens_in = response.usage.prompt_tokens if response.usage else 0
    tokens_out = response.usage.completion_tokens if response.usage else 0
    
    return content, tokens_in, tokens_out


def _parse_email_response(response: str, tokens_in: int, tokens_out: int) -> EmailDraft:
    """Parse and validate the LLM response."""
    
    # Strip any markdown code blocks
    clean_response = response.strip()
    if clean_response.startswith("```"):
        lines = clean_response.split("\n")
        clean_response = "\n".join(lines[1:-1])
    
    data = json.loads(clean_response)
    
    # Validate required fields
    if "email_subject" not in data:
        raise KeyError("Missing required field: email_subject")
    if "email_body" not in data:
        raise KeyError("Missing required field: email_body")
    
    # Validate lengths
    if len(data["email_subject"]) > 100:
        data["email_subject"] = data["email_subject"][:97] + "..."
    
    if len(data["email_body"]) > 2000:
        raise ValueError("Email body too long (>2000 chars)")
    
    return EmailDraft(
        subject=data["email_subject"],
        body=data["email_body"],
        follow_up_task=data.get("follow_up_task"),
        tokens_used=tokens_in + tokens_out,
        tokens_in=tokens_in,
        tokens_out=tokens_out,
        model_name=DRAFTING_MODEL.name,
        raw_response=response,
    )


def _personalize_draft(draft: EmailDraft, name: str) -> EmailDraft:
    """Ensure the email uses the correct name."""
    
    # Replace common placeholders
    body = draft.body
    placeholders = ["[Name]", "{name}", "{{name}}", "[name]", "{Name}"]
    
    for placeholder in placeholders:
        if placeholder in body:
            body = body.replace(placeholder, name or "there")
    
    # If "Hi there" and we have a name, personalize
    if name and "Hi there" in body:
        body = body.replace("Hi there", f"Hi {name}")
    
    return EmailDraft(
        subject=draft.subject,
        body=body,
        follow_up_task=draft.follow_up_task,
        tokens_used=draft.tokens_used,
        raw_response=draft.raw_response,
    )


def _format_enrichment(data: Optional[dict]) -> str:
    """Format enrichment data for prompt."""
    if not data:
        return "No additional context available"
    
    lines = []
    for key, value in data.items():
        if value:
            lines.append(f"{key}: {value}")
    
    return "\n".join(lines) if lines else "No additional context available"
