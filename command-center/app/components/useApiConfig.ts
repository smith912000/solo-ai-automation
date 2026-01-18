"use client";

import { useCallback, useEffect, useState } from "react";

export type ApiConfig = {
  apiKey: string;
  clientId: string;
  apiBase: string;
};

const DEFAULTS: ApiConfig = {
  apiKey: "",
  clientId: "",
  apiBase: "",
};

export function useApiConfig() {
  const [config, setConfig] = useState<ApiConfig>(DEFAULTS);

  useEffect(() => {
    const stored = {
      apiKey: localStorage.getItem("commandCenterApiKey") || "",
      clientId: localStorage.getItem("commandCenterClientId") || "",
      apiBase: localStorage.getItem("commandCenterApiBase") || "",
    };
    setConfig(stored);
  }, []);

  const updateConfig = useCallback((next: Partial<ApiConfig>) => {
    setConfig((current) => {
      const updated = { ...current, ...next };
      localStorage.setItem("commandCenterApiKey", updated.apiKey);
      localStorage.setItem("commandCenterClientId", updated.clientId);
      localStorage.setItem("commandCenterApiBase", updated.apiBase);
      return updated;
    });
  }, []);

  const buildHeaders = useCallback(() => {
    const headers: Record<string, string> = {};
    if (config.apiKey) {
      headers["X-API-Key"] = config.apiKey;
    }
    if (config.clientId) {
      headers["X-Client-Id"] = config.clientId;
    }
    return headers;
  }, [config.apiKey, config.clientId]);

  const apiBase = config.apiBase || process.env.NEXT_PUBLIC_API_BASE || "";

  return { config, updateConfig, buildHeaders, apiBase };
}
