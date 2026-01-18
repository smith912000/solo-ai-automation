"""
Lead Qualifier - Lead Scoring Logic

This module handles the LLM-powered lead qualification.
"""

import json
import logging
from typing import Optional
from dataclasses import dataclass

from .config import (
    REASONING_MODEL,
    QUALIFICATION_PROMPT,
    QUALIFICATION_RUBRIC,
    QUALIFICATION_OUTPUT_SCHEMA,
    DEFAULT_OFFER,
    MAX_RETRIES_PER_STEP,
)

logger = logging.getLogger(__name__)


@dataclass
class QualificationResult:
    """Structured result from lead qualification."""
    score: int
    label: str  # qualified, review, disqualified
    key_reason: str
    personalization_points: list[str]
    company_fit_score: int = 0
    intent_score: int = 0
    engagement_score: int = 0
    timing_score: int = 0
    tokens_used: int = 0
    tokens_in: int = 0
    tokens_out: int = 0
    model_name: Optional[str] = None
    raw_response: Optional[str] = None


def qualify_lead(
    name: str,
    email: str,
    company: Optional[str] = None,
    website: Optional[str] = None,
    message: Optional[str] = None,
    source: Optional[str] = None,
    enrichment_data: Optional[dict] = None,
    offer_description: Optional[str] = None,
    llm_client = None,
) -> QualificationResult:
    """
    Qualify a lead using LLM reasoning.
    
    Args:
        name: Contact name
        email: Contact email
        company: Company name (optional)
        website: Company website (optional)
        message: Form message (optional)
        source: Lead source (optional)
        enrichment_data: Dict of enrichment info (optional)
        offer_description: Custom offer description (optional)
        llm_client: OpenAI client instance (will create if not provided)
    
    Returns:
        QualificationResult with score, label, and personalization points
    
    Raises:
        ValueError: If LLM returns invalid response after retries
    """
    
    # Build prompt
    prompt = QUALIFICATION_PROMPT.format(
        offer_description=offer_description or DEFAULT_OFFER,
        rubric=QUALIFICATION_RUBRIC,
        name=name or "Unknown",
        email=email,
        company=company or "Not provided",
        website=website or "Not provided",
        message=message or "No message",
        source=source or "Unknown",
        enrichment_data=_format_enrichment(enrichment_data),
    )
    
    # Call LLM with retries
    last_error = None
    for attempt in range(MAX_RETRIES_PER_STEP + 1):
        try:
            response, tokens_in, tokens_out = _call_llm(prompt, llm_client)
            result = _parse_qualification_response(response, tokens_in, tokens_out)
            
            logger.info(
                f"Lead qualified: {email} -> {result.label} ({result.score})"
            )
            return result
            
        except (json.JSONDecodeError, KeyError, ValueError) as e:
            last_error = e
            logger.warning(
                f"Qualification attempt {attempt + 1} failed: {e}"
            )
            
            # Add instruction to return valid JSON on retry
            if attempt < MAX_RETRIES_PER_STEP:
                prompt += "\n\nIMPORTANT: Your previous response was not valid JSON. Respond ONLY with the JSON object."
    
    # All retries failed
    raise ValueError(f"Failed to qualify lead after {MAX_RETRIES_PER_STEP + 1} attempts: {last_error}")


def _call_llm(prompt: str, client = None) -> tuple[str, int, int]:
    """
    Call the LLM and return response + token count.
    
    Returns:
        Tuple of (response_text, total_tokens)
    """
    if client is None:
        # Import here to avoid dependency issues if not using OpenAI
        from openai import OpenAI
        client = OpenAI()
    
    response = client.chat.completions.create(
        model=REASONING_MODEL.name,
        messages=[
            {"role": "system", "content": "You are a lead qualification specialist. Respond only with valid JSON."},
            {"role": "user", "content": prompt}
        ],
        max_tokens=REASONING_MODEL.max_tokens,
        temperature=REASONING_MODEL.temperature,
    )
    
    content = response.choices[0].message.content or ""
    tokens_in = response.usage.prompt_tokens if response.usage else 0
    tokens_out = response.usage.completion_tokens if response.usage else 0
    
    return content, tokens_in, tokens_out


def _parse_qualification_response(response: str, tokens_in: int, tokens_out: int) -> QualificationResult:
    """
    Parse and validate the LLM response.
    
    Raises:
        json.JSONDecodeError: If response is not valid JSON
        KeyError: If required fields are missing
        ValueError: If values are out of range
    """
    # Strip any markdown code blocks
    clean_response = response.strip()
    if clean_response.startswith("```"):
        lines = clean_response.split("\n")
        clean_response = "\n".join(lines[1:-1])
    
    data = json.loads(clean_response)
    
    # Validate required fields
    required = ["qualification_score", "qualification_label", "key_reason", "personalization_points"]
    for field in required:
        if field not in data:
            raise KeyError(f"Missing required field: {field}")
    
    # Validate score range
    score = data["qualification_score"]
    if not (0 <= score <= 100):
        raise ValueError(f"Score {score} out of range 0-100")
    
    # Validate label
    label = data["qualification_label"]
    if label not in ("qualified", "review", "disqualified"):
        raise ValueError(f"Invalid label: {label}")
    
    # Ensure label matches score
    if score >= 70 and label != "qualified":
        label = "qualified"
    elif 40 <= score < 70 and label not in ("qualified", "review"):
        label = "review"
    elif score < 40 and label != "disqualified":
        label = "disqualified"
    
    return QualificationResult(
        score=score,
        label=label,
        key_reason=data["key_reason"],
        personalization_points=data.get("personalization_points", []),
        company_fit_score=data.get("company_fit_score", 0),
        intent_score=data.get("intent_score", 0),
        engagement_score=data.get("engagement_score", 0),
        timing_score=data.get("timing_score", 0),
        tokens_used=tokens_in + tokens_out,
        tokens_in=tokens_in,
        tokens_out=tokens_out,
        model_name=REASONING_MODEL.name,
        raw_response=response,
    )


def _format_enrichment(data: Optional[dict]) -> str:
    """Format enrichment data for prompt."""
    if not data:
        return "No enrichment data available"
    
    lines = []
    for key, value in data.items():
        if value:
            lines.append(f"{key}: {value}")
    
    return "\n".join(lines) if lines else "No enrichment data available"
