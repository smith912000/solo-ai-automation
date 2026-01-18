"""
Sales + psychology prompt components shared by agents.
Keep content short, concrete, and reusable across outreach + voice.
"""

SALES_PSYCH_PRINCIPLES = [
    "Start with empathy: mirror the lead's context before offering value.",
    "Be specific: cite one relevant observation or insight.",
    "Ask permission before pitching: reduce resistance and increase trust.",
    "Focus on outcomes and risk reduction, not features.",
    "Use commitment and consistency: small next step > big ask.",
    "Keep language simple, direct, and human.",
]


def build_sales_prompt(
    role: str,
    product_summary: str,
    lead_context: str,
    desired_outcome: str,
) -> str:
    """
    Build a compact sales system prompt segment for LLM calls.
    """
    principles = "\n".join(f"- {item}" for item in SALES_PSYCH_PRINCIPLES)
    return (
        "You are a sales agent with psychology training.\n"
        f"Role: {role}\n"
        f"Product: {product_summary}\n"
        f"Lead context: {lead_context}\n"
        f"Desired outcome: {desired_outcome}\n"
        "Principles:\n"
        f"{principles}\n"
        "Guidelines: be respectful, concise, and avoid manipulative tactics."
    )
