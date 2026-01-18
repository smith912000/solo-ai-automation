import os

from fastapi.testclient import TestClient

from api.main import app
from lib import db as db_lib


def _set_env():
    os.environ["API_KEY"] = "test-api-key"
    os.environ["DEFAULT_CLIENT_ID"] = "00000000-0000-0000-0000-000000000001"


def test_dashboard_stats(monkeypatch):
    _set_env()
    client = TestClient(app)

    monkeypatch.setattr(db_lib, "get_supabase_client", lambda: object())
    monkeypatch.setattr(db_lib, "get_queue_counts", lambda *_: {"queued": 1})
    monkeypatch.setattr(db_lib, "get_outbox_counts", lambda *_: {"queued": 2})
    monkeypatch.setattr(db_lib, "get_run_counts", lambda *_: {"success": 3})
    monkeypatch.setattr(db_lib, "list_recent_runs", lambda *_args, **_kwargs: [])
    monkeypatch.setattr(db_lib, "list_cost_events", lambda *_args, **_kwargs: [])

    response = client.get("/api/dashboard/stats", headers={"X-API-Key": "test-api-key"})
    assert response.status_code == 200
    data = response.json()
    assert data["queue"]["queued"] == 1
    assert data["outbox"]["queued"] == 2
    assert data["runs"]["success"] == 3


def test_pipeline(monkeypatch):
    _set_env()
    client = TestClient(app)
    monkeypatch.setattr(db_lib, "get_supabase_client", lambda: object())
    monkeypatch.setattr(
        db_lib,
        "list_crm_leads",
        lambda *_args, **_kwargs: [{"email": "test@example.com"}],
    )

    response = client.get("/api/pipeline", headers={"X-API-Key": "test-api-key"})
    assert response.status_code == 200
    data = response.json()
    assert data["items"][0]["email"] == "test@example.com"


def test_agents(monkeypatch):
    _set_env()
    client = TestClient(app)
    monkeypatch.setattr(db_lib, "get_supabase_client", lambda: object())
    monkeypatch.setattr(
        db_lib,
        "list_agent_runs",
        lambda *_args, **_kwargs: [
            {"agent_name": "sales", "status": "success", "started_at": "now"}
        ],
    )

    response = client.get("/api/agents", headers={"X-API-Key": "test-api-key"})
    assert response.status_code == 200
    data = response.json()
    assert data["items"][0]["agent_name"] == "sales"


def test_approvals(monkeypatch):
    _set_env()
    client = TestClient(app)
    monkeypatch.setattr(db_lib, "get_supabase_client", lambda: object())
    monkeypatch.setattr(
        db_lib,
        "list_outbox_emails",
        lambda *_args, **_kwargs: [{"id": "outbox-1"}],
    )

    response = client.get("/api/approvals", headers={"X-API-Key": "test-api-key"})
    assert response.status_code == 200
    data = response.json()
    assert data["items"][0]["id"] == "outbox-1"


def test_analytics_costs(monkeypatch):
    _set_env()
    client = TestClient(app)
    monkeypatch.setattr(db_lib, "get_supabase_client", lambda: object())
    monkeypatch.setattr(
        db_lib,
        "list_cost_events",
        lambda *_args, **_kwargs: [{"category": "llm", "cost_usd": 2.5}],
    )

    response = client.get("/api/analytics/costs", headers={"X-API-Key": "test-api-key"})
    assert response.status_code == 200
    data = response.json()
    assert data["by_category"]["llm"] == 2.5
