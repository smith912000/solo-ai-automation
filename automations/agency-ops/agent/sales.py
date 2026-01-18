from lib.training import build_sales_prompt, build_objection_prompt


def handle(payload: dict) -> dict:
    lead_name = payload.get("name", "there")
    company = payload.get("company", "your business")
    product_summary = payload.get("product_summary", "AI automation services")
    lead_context = payload.get("lead_context", "Inbound interest")
    desired_outcome = payload.get("desired_outcome", "Book a short discovery call")
    objection = payload.get("objection")

    sales_prompt = build_sales_prompt(
        role="sales_outreach",
        product_summary=product_summary,
        lead_context=lead_context,
        desired_outcome=desired_outcome,
    )
    objection_prompt = build_objection_prompt(objection) if objection else ""

    message = (
        f"Hi {lead_name}, I noticed {company} might benefit from {product_summary}. "
        f"Would it be helpful to share a 2-minute summary and see if a short call makes sense?"
    )

    return {
        "status": "ok",
        "message": message,
        "sales_prompt": sales_prompt,
        "objection_prompt": objection_prompt,
        "next_action": "schedule_call",
    }
