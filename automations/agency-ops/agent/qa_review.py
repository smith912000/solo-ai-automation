def handle(payload: dict) -> dict:
    artifact = payload.get("artifact", "automation_output")
    criteria = payload.get("criteria", "quality_checklist")
    return {
        "status": "ok",
        "summary": "QA review staged",
        "artifact": artifact,
        "criteria": criteria,
        "next_action": "run_quality_review",
    }
