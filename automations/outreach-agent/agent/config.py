import os
from dataclasses import dataclass


@dataclass
class ModelConfig:
    name: str
    max_tokens: int
    temperature: float


OUTREACH_MODEL = ModelConfig(
    name=os.getenv("OUTREACH_MODEL", "gpt-4o-mini"),
    max_tokens=1200,
    temperature=0.6,
)


COLD_EMAIL_PROMPT = """You are an expert cold outreach copywriter.

Goal: Draft a short, personalized email that starts a conversation.

Prospect:
- Name: {name}
- Role: {role}
- Company: {company}
- Website: {website}
- Pain points: {pain_points}
- Notes: {notes}

Guidelines:
1. Subject line < 8 words.
2. Body <= 150 words.
3. Use a calm, professional tone.
4. Single CTA (ask for a short call).
5. Avoid hype or spammy language.

Respond with ONLY valid JSON:
{{
  "email_subject": "<subject>",
  "email_body": "<body>",
  "follow_up_task": "<optional follow-up>"
}}
"""
