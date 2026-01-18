from lib.training import build_sales_prompt


def handle(payload: dict) -> dict:
    customer = payload.get("customer", "Client")
    issue = payload.get("issue", "General inquiry")
    desired_outcome = payload.get("desired_outcome", "Resolve and confirm satisfaction")
    product_summary = payload.get("product_summary", "your automation program")

    support_prompt = build_sales_prompt(
        role="support",
        product_summary=product_summary,
        lead_context=issue,
        desired_outcome=desired_outcome,
    )

    response = (
        f"Hi {customer}, thanks for the details. "
        "I can help with that and will confirm once it's resolved."
    )

    return {
        "status": "ok",
        "response": response,
        "support_prompt": support_prompt,
        "next_action": "resolve_issue",
    }
