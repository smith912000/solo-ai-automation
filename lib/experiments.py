from datetime import datetime, timedelta
from typing import Optional

from supabase import Client

from lib import db as db_lib


def evaluate_experiment(
    db: Client,
    experiment_id: str,
    results: Optional[dict] = None,
    status: str = "completed",
) -> dict:
    if results is None:
        results = {"note": "No results provided", "confidence": 0.0}
    db_lib.update_experiment(db, experiment_id, status=status, results=results)
    return {"status": "ok", "experiment_id": experiment_id, "results": results}


def review_optimization(
    db: Client,
    client_id: str,
    period_hours: int = 24,
    max_cost_usd: Optional[float] = None,
    max_cost_per_run: Optional[float] = None,
) -> dict:
    end_dt = datetime.utcnow()
    start_dt = end_dt - timedelta(hours=period_hours)
    cost_events = db_lib.list_cost_events(
        db,
        client_id=client_id,
        start_at=start_dt.isoformat(),
        end_at=end_dt.isoformat(),
    )
    total_cost = sum(float(event.get("cost_usd") or 0) for event in cost_events)
    run_counts = db_lib.get_run_counts(db, client_id)
    run_total = sum(run_counts.values())
    cost_per_run = (total_cost / run_total) if run_total > 0 else 0.0

    alerts = []
    if max_cost_usd is not None and total_cost > max_cost_usd:
        alerts.append("cost_exceeded")
    if max_cost_per_run is not None and cost_per_run > max_cost_per_run:
        alerts.append("cost_per_run_exceeded")

    return {
        "status": "ok",
        "period_hours": period_hours,
        "total_cost_usd": total_cost,
        "cost_per_run_usd": cost_per_run,
        "run_total": run_total,
        "alerts": alerts,
    }
