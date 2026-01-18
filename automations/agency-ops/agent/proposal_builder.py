def handle(payload: dict) -> dict:
    scope = payload.get("scope", "Standard automation package")
    budget = payload.get("budget", "TBD")
    return {
        "status": "ok",
        "summary": "Proposal outline drafted",
        "scope": scope,
        "budget": budget,
        "next_action": "draft_proposal",
    }
