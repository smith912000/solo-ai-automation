def handle(payload: dict) -> dict:
    experiment = payload.get("experiment", "Test subject line variant A/B")
    metric = payload.get("metric", "reply_rate")
    target = payload.get("target", 0.1)
    return {
        "status": "ok",
        "summary": "Growth experiment staged",
        "experiment": experiment,
        "metric": metric,
        "target": target,
        "next_action": "run_experiment",
    }
