"use client";

import { useEffect, useState } from "react";
import ApiControls from "./components/ApiControls";
import { useApiConfig } from "./components/useApiConfig";

type DashboardStats = {
  queue?: Record<string, number>;
  outbox?: Record<string, number>;
  runs?: Record<string, number>;
  recent_runs?: unknown[];
  costs?: { total_usd: number; count: number };
};

export default function DashboardPage() {
  const { apiBase, buildHeaders } = useApiConfig();
  const [data, setData] = useState<DashboardStats | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchStats = async () => {
      try {
        const response = await fetch(`${apiBase}/api/dashboard/stats`, {
          headers: buildHeaders(),
        });
        if (!response.ok) {
          throw new Error(`Failed: ${response.status}`);
        }
        const payload = await response.json();
        setData(payload);
        setError(null);
      } catch (err) {
        setError(String(err));
      }
    };
    fetchStats();
  }, [apiBase, buildHeaders]);

  return (
    <section>
      <div className="row">
        <ApiControls />
        <div className="card">
          <strong>Snapshot</strong>
          <div className="muted">
            Costs: ${data?.costs?.total_usd?.toFixed(2) ?? "0.00"} (events:{" "}
            {data?.costs?.count ?? 0})
          </div>
          {error && <div className="muted">{error}</div>}
        </div>
      </div>

      <div className="row">
        <div className="card">
          <strong>Queue</strong>
          <div className="muted">{JSON.stringify(data?.queue ?? {})}</div>
        </div>
        <div className="card">
          <strong>Outbox</strong>
          <div className="muted">{JSON.stringify(data?.outbox ?? {})}</div>
        </div>
        <div className="card">
          <strong>Runs</strong>
          <div className="muted">{JSON.stringify(data?.runs ?? {})}</div>
        </div>
      </div>

      <div className="card">
        <strong>Recent Runs</strong>
        <pre>{JSON.stringify(data?.recent_runs ?? [], null, 2)}</pre>
      </div>
    </section>
  );
}
