"""
Objection handling playbook blocks for consistent responses.
"""

OBJECTION_PLAYBOOK = {
    "not_interested": [
        "Acknowledge and reduce pressure: 'No worries, I can be brief.'",
        "Offer a relevant, single-sentence value point.",
        "Ask a low-commitment question or provide a graceful exit.",
    ],
    "too_expensive": [
        "Acknowledge budget constraints and ask about target outcome.",
        "Reframe with ROI or risk reduction in one sentence.",
        "Offer a smaller pilot or phased option.",
    ],
    "already_have_solution": [
        "Respect existing solution; ask what they like about it.",
        "Position as complementary or a measurable improvement.",
        "Suggest a quick comparison or benchmark.",
    ],
    "no_time": [
        "Confirm timing is bad and propose a short follow-up window.",
        "Offer an async summary or 2-minute overview.",
    ],
}


def build_objection_prompt(objection_key: str) -> str:
    """
    Return a concise prompt block for a given objection type.
    """
    steps = OBJECTION_PLAYBOOK.get(objection_key, [])
    steps_text = "\n".join(f"- {step}" for step in steps) or "- Ask a clarifying question."
    return (
        "Handle the objection with empathy and brevity.\n"
        f"Objection: {objection_key}\n"
        "Response steps:\n"
        f"{steps_text}"
    )
