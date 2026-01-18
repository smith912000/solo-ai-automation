def handle(payload: dict) -> dict:
    account = payload.get("account", "Client")
    health = payload.get("health", "unknown")
    return {
        "status": "ok",
        "summary": "Client success review queued",
        "account": account,
        "health": health,
        "next_action": "review_success",
    }
