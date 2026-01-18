from fastapi import APIRouter
from fastapi.responses import HTMLResponse


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
