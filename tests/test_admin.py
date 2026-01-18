import os

from fastapi.testclient import TestClient

from api.main import app
from lib import db as db_lib


def _set_env():
    os.environ["API_KEY"] = "test-api-key"
    os.environ["DEFAULT_CLIENT_ID"] = "00000000-0000-0000-0000-000000000001"


def test_admin_metrics(monkeypatch):
    _set_env()
    client = TestClient(app)

    monkeypatch.setattr(db_lib, "get_supabase_client", lambda: object())
    monkeypatch.setattr(db_lib, "get_queue_counts", lambda *_: {"queued": 1})
    monkeypatch.setattr(db_lib, "get_outbox_counts", lambda *_: {"queued": 2})
    monkeypatch.setattr(db_lib, "get_run_counts", lambda *_: {"success": 3})
    monkeypatch.setattr(db_lib, "list_recent_runs", lambda *_args, **_kwargs: [])

    response = client.get(
        "/admin/metrics",
        headers={"X-API-Key": "test-api-key"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["queue"]["queued"] == 1
    assert data["outbox"]["queued"] == 2
    assert data["runs"]["success"] == 3


def test_admin_outbox(monkeypatch):
    _set_env()
    client = TestClient(app)

    monkeypatch.setattr(db_lib, "get_supabase_client", lambda: object())
    monkeypatch.setattr(
        db_lib,
        "list_outbox_emails",
        lambda *_args, **_kwargs: [{"id": "outbox-1"}],
    )

    response = client.get(
        "/admin/outbox",
        headers={"X-API-Key": "test-api-key"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["items"][0]["id"] == "outbox-1"
