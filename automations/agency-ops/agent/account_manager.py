def handle(payload: dict) -> dict:
    account = payload.get("account", "Client")
    objective = payload.get("objective", "Maintain relationship health")
    return {
        "status": "ok",
        "summary": "Account check-in prepared",
        "account": account,
        "objective": objective,
        "next_action": "schedule_checkin",
    }
