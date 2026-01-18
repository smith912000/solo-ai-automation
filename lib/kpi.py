from datetime import datetime, timedelta
from typing import Optional

from supabase import Client

from lib import db as db_lib


def collect_kpi_snapshot(
    db: Client,
    client_id: str,
    period_start: Optional[str] = None,
    period_end: Optional[str] = None,
) -> dict:
    end_dt = datetime.utcnow() if not period_end else datetime.fromisoformat(period_end)
    start_dt = (
        end_dt - timedelta(days=1)
        if not period_start
        else datetime.fromisoformat(period_start)
    )

    runs = db_lib.get_run_counts(db, client_id)
    outbox = db_lib.get_outbox_counts(db, client_id)
    queue = db_lib.get_queue_counts(db)
    cost_events = db_lib.list_cost_events(
        db,
        client_id=client_id,
        start_at=start_dt.isoformat(),
        end_at=end_dt.isoformat(),
    )
    cost_by_category: dict[str, float] = {}
    total_cost = 0.0
    for event in cost_events:
        cost = float(event.get("cost_usd") or 0)
        category = event.get("category") or "unknown"
        cost_by_category[category] = cost_by_category.get(category, 0.0) + cost
        total_cost += cost

    metrics = {
        "runs": runs,
        "outbox": outbox,
        "queue": queue,
        "costs": {
            "total_usd": total_cost,
            "by_category": cost_by_category,
            "count": len(cost_events),
        },
        "period_seconds": int((end_dt - start_dt).total_seconds()),
    }

    return db_lib.create_kpi_snapshot(
        db,
        client_id=client_id,
        period_start=start_dt.isoformat(),
        period_end=end_dt.isoformat(),
        metrics=metrics,
    )
