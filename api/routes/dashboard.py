import os
from typing import Optional

from fastapi import APIRouter, Header, HTTPException
from fastapi.responses import HTMLResponse

from lib import db as db_lib
from lib.auth import require_api_key


router = APIRouter(tags=["dashboard"])


@router.get("/dashboard", response_class=HTMLResponse)
def dashboard():
    html = """
<!doctype html>
<html>
  <head>
    <meta charset="utf-8" />
    <title>Command Center</title>
    <style>
      body { font-family: Arial, sans-serif; margin: 24px; color: #111; }
      h1 { margin-bottom: 8px; }
      .row { display: flex; gap: 16px; flex-wrap: wrap; }
      .card { border: 1px solid #ddd; padding: 12px 16px; border-radius: 8px; min-width: 200px; }
      .muted { color: #666; }
      pre { background: #f7f7f7; padding: 12px; border-radius: 8px; overflow: auto; }
      input { padding: 6px 8px; min-width: 240px; }
      button { padding: 6px 12px; }
    </style>
  </head>
  <body>
    <h1>Command Center</h1>
    <p class="muted">Live operations view for the Lead Qualifier automation.</p>

    <div class="row">
      <div class="card">
        <div><strong>API Key</strong></div>
        <input id="apiKey" type="password" placeholder="X-API-Key" />
        <div style="height: 8px;"></div>
        <div><strong>Client ID (optional)</strong></div>
        <input id="clientId" type="text" placeholder="DEFAULT_CLIENT_ID" />
        <div style="height: 8px;"></div>
        <button onclick="loadMetrics()">Load Metrics</button>
      </div>
      <div class="card">
        <div><strong>Queue</strong></div>
        <div id="queueCounts" class="muted">Not loaded</div>
      </div>
      <div class="card">
        <div><strong>Outbox</strong></div>
        <div id="outboxCounts" class="muted">Not loaded</div>
      </div>
      <div class="card">
        <div><strong>Runs</strong></div>
        <div id="runCounts" class="muted">Not loaded</div>
      </div>
    </div>

    <h2>Recent Runs</h2>
    <pre id="recentRuns">Not loaded</pre>

    <h2>Approvals</h2>
    <div class="card">
      <div><strong>Status</strong></div>
      <div class="muted">Locked — approvals UI is not enabled yet.</div>
      <div class="muted">Use `/admin/outbox` endpoints for now.</div>
    </div>

    <h2>Pipeline</h2>
    <div class="card">
      <div><strong>Status</strong></div>
      <div class="muted">Locked — pipeline UI coming next.</div>
    </div>

    <h2>Agents</h2>
    <div class="card">
      <div><strong>Status</strong></div>
      <div class="muted">Locked — agent controls coming next.</div>
    </div>

    <script>
      let refreshTimer = null;

      function formatCounts(obj) {
        if (!obj) return "N/A";
        return Object.keys(obj).map(k => k + ": " + obj[k]).join(", ");
      }

      async function loadMetrics() {
        const apiKey = document.getElementById("apiKey").value;
        const clientId = document.getElementById("clientId").value;

        if (!apiKey) {
          alert("API key required.");
          return;
        }

        const headers = { "X-API-Key": apiKey };
        if (clientId) headers["X-Client-Id"] = clientId;

        try {
          const res = await fetch("/admin/metrics", { headers });
          if (!res.ok) {
            throw new Error("Failed to load metrics: " + res.status);
          }
          const data = await res.json();
          document.getElementById("queueCounts").innerText = formatCounts(data.queue);
          document.getElementById("outboxCounts").innerText = formatCounts(data.outbox);
          document.getElementById("runCounts").innerText = formatCounts(data.runs);
          document.getElementById("recentRuns").innerText = JSON.stringify(data.recent_runs, null, 2);

          if (!refreshTimer) {
            refreshTimer = setInterval(loadMetrics, 30000);
          }
        } catch (err) {
          document.getElementById("recentRuns").innerText = String(err);
        }
      }
    </script>
  </body>
</html>
    """
    return HTMLResponse(content=html)


@router.get("/api/dashboard/stats")
def dashboard_stats(
    x_client_id: Optional[str] = Header(default=None),
    x_api_key: Optional[str] = Header(default=None),
):
    require_api_key(x_api_key, admin=True)
    client_id = x_client_id or os.getenv("DEFAULT_CLIENT_ID")
    if not client_id:
        raise HTTPException(status_code=500, detail="DEFAULT_CLIENT_ID is not set")
    db = db_lib.get_supabase_client()
    costs = db_lib.list_cost_events(db, client_id, limit=200)
    total_cost = sum(float(item.get("cost_usd") or 0) for item in costs)
    return {
        "queue": db_lib.get_queue_counts(db),
        "outbox": db_lib.get_outbox_counts(db, client_id),
        "runs": db_lib.get_run_counts(db, client_id),
        "recent_runs": db_lib.list_recent_runs(db, client_id, limit=15),
        "costs": {"total_usd": total_cost, "count": len(costs)},
    }


@router.get("/api/pipeline")
def pipeline(
    x_client_id: Optional[str] = Header(default=None),
    x_api_key: Optional[str] = Header(default=None),
    limit: int = 100,
):
    require_api_key(x_api_key, admin=True)
    client_id = x_client_id or os.getenv("DEFAULT_CLIENT_ID")
    if not client_id:
        raise HTTPException(status_code=500, detail="DEFAULT_CLIENT_ID is not set")
    db = db_lib.get_supabase_client()
    leads = db_lib.list_crm_leads(db, client_id, limit=limit)
    return {"items": leads}


@router.get("/api/agents")
def list_agents(
    x_client_id: Optional[str] = Header(default=None),
    x_api_key: Optional[str] = Header(default=None),
    limit: int = 200,
):
    require_api_key(x_api_key, admin=True)
    client_id = x_client_id or os.getenv("DEFAULT_CLIENT_ID")
    if not client_id:
        raise HTTPException(status_code=500, detail="DEFAULT_CLIENT_ID is not set")
    db = db_lib.get_supabase_client()
    runs = db_lib.list_agent_runs(db, client_id, limit=limit)
    agents: dict[str, dict] = {}
    for run in runs:
        name = run.get("agent_name") or "unknown"
        current = agents.setdefault(
            name,
            {"agent_name": name, "runs": 0, "last_status": None, "last_run": None},
        )
        current["runs"] += 1
        if not current["last_run"]:
            current["last_status"] = run.get("status")
            current["last_run"] = run
    return {"items": list(agents.values())}


@router.get("/api/agents/{agent_name}/runs")
def agent_runs(
    agent_name: str,
    x_client_id: Optional[str] = Header(default=None),
    x_api_key: Optional[str] = Header(default=None),
    limit: int = 50,
):
    require_api_key(x_api_key, admin=True)
    client_id = x_client_id or os.getenv("DEFAULT_CLIENT_ID")
    if not client_id:
        raise HTTPException(status_code=500, detail="DEFAULT_CLIENT_ID is not set")
    db = db_lib.get_supabase_client()
    runs = db_lib.list_agent_runs(db, client_id, agent_name=agent_name, limit=limit)
    return {"items": runs}


@router.get("/api/approvals")
def approvals(
    x_client_id: Optional[str] = Header(default=None),
    x_api_key: Optional[str] = Header(default=None),
    limit: int = 50,
):
    require_api_key(x_api_key, admin=True)
    client_id = x_client_id or os.getenv("DEFAULT_CLIENT_ID")
    if not client_id:
        raise HTTPException(status_code=500, detail="DEFAULT_CLIENT_ID is not set")
    db = db_lib.get_supabase_client()
    items = db_lib.list_outbox_emails(db, client_id, status="queued", limit=limit)
    return {"items": items}


@router.get("/api/analytics/revenue")
def analytics_revenue(
    x_api_key: Optional[str] = Header(default=None),
):
    require_api_key(x_api_key, admin=True)
    return {"total_usd": 0.0, "note": "Revenue tracking not configured yet"}


@router.get("/api/analytics/costs")
def analytics_costs(
    x_client_id: Optional[str] = Header(default=None),
    x_api_key: Optional[str] = Header(default=None),
    start_at: Optional[str] = None,
    end_at: Optional[str] = None,
):
    require_api_key(x_api_key, admin=True)
    client_id = x_client_id or os.getenv("DEFAULT_CLIENT_ID")
    if not client_id:
        raise HTTPException(status_code=500, detail="DEFAULT_CLIENT_ID is not set")
    db = db_lib.get_supabase_client()
    events = db_lib.list_cost_events(
        db,
        client_id=client_id,
        start_at=start_at,
        end_at=end_at,
    )
    total_cost = 0.0
    by_category: dict[str, float] = {}
    for event in events:
        cost = float(event.get("cost_usd") or 0)
        category = event.get("category") or "unknown"
        by_category[category] = by_category.get(category, 0.0) + cost
        total_cost += cost
    return {"total_usd": total_cost, "by_category": by_category, "count": len(events)}
