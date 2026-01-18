def handle(payload: dict) -> dict:
    task = payload.get("task", "Review operational checklist")
    context = payload.get("context", {})
    return {
        "status": "ok",
        "summary": "Ops task queued",
        "task": task,
        "context": context,
        "next_action": "execute_task",
    }
