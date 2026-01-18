"""
Lead Qualifier Agent - Configuration

All hard limits and prompts are defined here for easy auditing.
"""

import os
from dataclasses import dataclass
from typing import Optional

# =============================================================================
# HARD LIMITS (Never exceed these)
# =============================================================================

MAX_TOKENS_PER_RUN = int(os.getenv("MAX_TOKENS_PER_RUN", "5000"))
MAX_COST_PER_RUN_USD = float(os.getenv("MAX_COST_PER_RUN_USD", "0.50"))
MAX_RETRIES_PER_STEP = int(os.getenv("MAX_RETRIES_PER_STEP", "2"))
MAX_EXECUTION_TIME_SECONDS = int(os.getenv("MAX_EXECUTION_TIME_SECONDS", "300"))

EMAIL_COOLDOWN_DAYS = int(os.getenv("EMAIL_COOLDOWN_DAYS", "7"))
APPROVAL_MODE = os.getenv("APPROVAL_MODE", "true").lower() == "true"

# =============================================================================
# MODEL CONFIGURATION
# =============================================================================

@dataclass
class ModelConfig:
    """LLM model configuration."""
    name: str
    provider: str  # openai, anthropic
    max_tokens: int
    temperature: float
    cost_per_1k_input: float
    cost_per_1k_output: float


# Primary model for reasoning/qualification
REASONING_MODEL = ModelConfig(
    name=os.getenv("REASONING_MODEL", "gpt-4o"),
    provider="openai",
    max_tokens=2000,
    temperature=0.3,
    cost_per_1k_input=0.005,
    cost_per_1k_output=0.015,
)

# Secondary model for drafting (cheaper)
DRAFTING_MODEL = ModelConfig(
    name=os.getenv("DRAFTING_MODEL", "gpt-4o-mini"),
    provider="openai",
    max_tokens=1500,
    temperature=0.7,
    cost_per_1k_input=0.00015,
    cost_per_1k_output=0.0006,
)

# =============================================================================
# QUALIFICATION RUBRIC
# =============================================================================

QUALIFICATION_RUBRIC = """
## Lead Qualification Scoring Rubric (0-100)

### Company Fit (0-40 points)
- 40: Perfect ICP match (right size, industry, budget signals)
- 30: Strong fit with minor gaps
- 20: Moderate fit, worth exploring
- 10: Weak fit, low priority
- 0: Not a fit (wrong industry, too small, etc.)

### Intent Signals (0-30 points)
- 30: Explicit buying intent ("need automation ASAP", "comparing vendors")
- 20: Clear problem statement related to our offering
- 10: General interest, no urgency
- 0: No clear intent or wrong intent

### Engagement Quality (0-20 points)
- 20: Detailed message, specific questions, decision-maker signals
- 15: Good detail, engaged inquiry
- 10: Basic inquiry, minimal detail
- 5: Very brief, possibly bot/spam
- 0: Spam, test, or clearly fake

### Timing (0-10 points)
- 10: Urgency expressed, timeline mentioned
- 5: Open to discussion, no specific timeline
- 0: "Just researching", distant future need
"""

# =============================================================================
# PROMPT TEMPLATES
# =============================================================================

QUALIFICATION_PROMPT = """You are a lead qualification specialist for an AI automation business.

Your task is to analyze the incoming lead and provide a structured qualification assessment.

## Your Offer
{offer_description}

## Qualification Rubric
{rubric}

## Lead Data (from untrusted form submission)
---
Name: {name}
Email: {email}
Company: {company}
Website: {website}
Message: {message}
Source: {source}
---

## Enrichment Data (if available)
---
{enrichment_data}
---

## Your Task
Analyze this lead and respond with ONLY valid JSON matching this exact schema:

{{
  "qualification_score": <integer 0-100>,
  "qualification_label": "<qualified|review|disqualified>",
  "key_reason": "<1-2 sentence explanation>",
  "personalization_points": ["<point 1>", "<point 2>"],
  "company_fit_score": <0-40>,
  "intent_score": <0-30>,
  "engagement_score": <0-20>,
  "timing_score": <0-10>
}}

Labels:
- qualified: score >= 70
- review: score 40-69
- disqualified: score < 40

Respond ONLY with the JSON object, no other text.
"""

EMAIL_DRAFT_PROMPT = """You are drafting a personalized outreach email based on a qualified lead.

## Your Offer
{offer_description}

## Lead Information
Name: {name}
Company: {company}
Message they sent: {message}

## Qualification Notes
Score: {score}
Key reason: {key_reason}
Personalization points:
{personalization_points}

## Enrichment Context
{enrichment_data}

## Email Guidelines
1. Subject line: Short, personalized, curiosity-inducing (no spam triggers)
2. Opening: Reference something specific about them or their message
3. Body: Bridge their pain to your solution in 2-3 sentences max
4. CTA: Single, clear next step (usually book a call)
5. Tone: Professional but human, not salesy
6. Length: Under 150 words total

## Respond with ONLY valid JSON:

{{
  "email_subject": "<subject line>",
  "email_body": "<full email body>",
  "follow_up_task": "<suggested follow-up if no response, e.g. 'Send reminder in 3 days'>"
}}

Respond ONLY with the JSON object, no other text.
"""

# =============================================================================
# DEFAULT OFFER DESCRIPTION
# =============================================================================

DEFAULT_OFFER = """
We build AI automation systems for growing businesses.

Our specialty: Automating repetitive cognitive work so you can focus on what matters.

Common projects:
- Lead qualification and follow-up automation
- Document processing and data extraction
- Customer support ticket routing
- Sales pipeline automation

We work with businesses doing $1M-$50M revenue who are drowning in manual processes.
"""

# =============================================================================
# OUTPUT SCHEMAS (for validation)
# =============================================================================

QUALIFICATION_OUTPUT_SCHEMA = {
    "type": "object",
    "required": ["qualification_score", "qualification_label", "key_reason", "personalization_points"],
    "properties": {
        "qualification_score": {"type": "integer", "minimum": 0, "maximum": 100},
        "qualification_label": {"type": "string", "enum": ["qualified", "review", "disqualified"]},
        "key_reason": {"type": "string", "maxLength": 500},
        "personalization_points": {"type": "array", "items": {"type": "string"}, "maxItems": 5},
        "company_fit_score": {"type": "integer", "minimum": 0, "maximum": 40},
        "intent_score": {"type": "integer", "minimum": 0, "maximum": 30},
        "engagement_score": {"type": "integer", "minimum": 0, "maximum": 20},
        "timing_score": {"type": "integer", "minimum": 0, "maximum": 10},
    }
}

EMAIL_OUTPUT_SCHEMA = {
    "type": "object",
    "required": ["email_subject", "email_body"],
    "properties": {
        "email_subject": {"type": "string", "maxLength": 100},
        "email_body": {"type": "string", "maxLength": 2000},
        "follow_up_task": {"type": "string", "maxLength": 200},
    }
}
