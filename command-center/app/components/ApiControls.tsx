"use client";

import { useApiConfig } from "./useApiConfig";

export default function ApiControls() {
  const { config, updateConfig } = useApiConfig();

  return (
    <div className="card">
      <div>
        <strong>API Base (optional)</strong>
      </div>
      <input
        type="text"
        placeholder="http://localhost:8000"
        value={config.apiBase}
        onChange={(event) => updateConfig({ apiBase: event.target.value })}
      />
      <div style={{ height: 8 }} />
      <div>
        <strong>API Key</strong>
      </div>
      <input
        type="password"
        placeholder="X-API-Key"
        value={config.apiKey}
        onChange={(event) => updateConfig({ apiKey: event.target.value })}
      />
      <div style={{ height: 8 }} />
      <div>
        <strong>Client ID (optional)</strong>
      </div>
      <input
        type="text"
        placeholder="DEFAULT_CLIENT_ID"
        value={config.clientId}
        onChange={(event) => updateConfig({ clientId: event.target.value })}
      />
    </div>
  );
}
