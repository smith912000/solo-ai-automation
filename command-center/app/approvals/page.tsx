"use client";

import { useEffect, useState } from "react";
import ApiControls from "../components/ApiControls";
import { useApiConfig } from "../components/useApiConfig";

export default function ApprovalsPage() {
  const { apiBase, buildHeaders } = useApiConfig();
  const [items, setItems] = useState<unknown[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchApprovals = async () => {
      try {
        const response = await fetch(`${apiBase}/api/approvals`, {
          headers: buildHeaders(),
        });
        if (!response.ok) {
          throw new Error(`Failed: ${response.status}`);
        }
        const payload = await response.json();
        setItems(payload.items || []);
        setError(null);
      } catch (err) {
        setError(String(err));
      }
    };
    fetchApprovals();
  }, [apiBase, buildHeaders]);

  return (
    <section>
      <ApiControls />
      <div className="card">
        <strong>Approval Queue</strong>
        {error && <div className="muted">{error}</div>}
        <pre>{JSON.stringify(items, null, 2)}</pre>
      </div>
    </section>
  );
}
