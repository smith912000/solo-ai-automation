def handle(payload: dict) -> dict:
    deliverable = payload.get("deliverable", "Automation rollout")
    timeline = payload.get("timeline", "TBD")
    return {
        "status": "ok",
        "summary": "Delivery plan staged",
        "deliverable": deliverable,
        "timeline": timeline,
        "next_action": "plan_delivery",
    }
