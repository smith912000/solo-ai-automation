"use client";

import { useEffect, useState } from "react";
import ApiControls from "../components/ApiControls";
import { useApiConfig } from "../components/useApiConfig";

type AnalyticsData = {
  revenue?: unknown;
  costs?: unknown;
};

export default function AnalyticsPage() {
  const { apiBase, buildHeaders } = useApiConfig();
  const [data, setData] = useState<AnalyticsData>({});
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchAnalytics = async () => {
      try {
        const headers = buildHeaders();
        const [revenueRes, costsRes] = await Promise.all([
          fetch(`${apiBase}/api/analytics/revenue`, { headers }),
          fetch(`${apiBase}/api/analytics/costs`, { headers }),
        ]);
        if (!revenueRes.ok || !costsRes.ok) {
          throw new Error("Failed to load analytics");
        }
        const revenue = await revenueRes.json();
        const costs = await costsRes.json();
        setData({ revenue, costs });
        setError(null);
      } catch (err) {
        setError(String(err));
      }
    };
    fetchAnalytics();
  }, [apiBase, buildHeaders]);

  return (
    <section>
      <ApiControls />
      <div className="card">
        <strong>Analytics</strong>
        {error && <div className="muted">{error}</div>}
        <pre>{JSON.stringify(data, null, 2)}</pre>
      </div>
    </section>
  );
}
