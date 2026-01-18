import os

from fastapi.testclient import TestClient

from api.main import app
from lib import db as db_lib


def _set_env():
    os.environ["API_KEY"] = "test-api-key"
    os.environ["DEFAULT_CLIENT_ID"] = "00000000-0000-0000-0000-000000000001"


def test_intake_valid_payload(monkeypatch):
    _set_env()
    client = TestClient(app)

    monkeypatch.setattr(db_lib, "get_supabase_client", lambda: object())
    monkeypatch.setattr(db_lib, "get_run_by_idempotency", lambda *_: None)
    monkeypatch.setattr(db_lib, "create_run", lambda *_args, **_kwargs: {"id": "run-1"})
    monkeypatch.setattr(db_lib, "enqueue_job", lambda *_args, **_kwargs: {"id": "job-1"})

    payload = {
        "name": "Test User",
        "email": "test@example.com",
        "company": "Acme",
        "message": "Hello",
    }
    response = client.post(
        "/webhook/lead",
        json=payload,
        headers={"X-API-Key": "test-api-key"},
    )
    assert response.status_code == 202
    data = response.json()
    assert data["status"] == "queued"
    assert data["run_id"] == "run-1"
    assert data["job_id"] == "job-1"


def test_intake_duplicate_detection(monkeypatch):
    _set_env()
    client = TestClient(app)

    monkeypatch.setattr(db_lib, "get_supabase_client", lambda: object())
    monkeypatch.setattr(
        db_lib, "get_run_by_idempotency", lambda *_: {"id": "run-dup"}
    )

    payload = {
        "name": "Test User",
        "email": "test@example.com",
        "timestamp": "2026-01-18T00:00:00Z",
    }
    response = client.post(
        "/webhook/lead",
        json=payload,
        headers={"X-API-Key": "test-api-key"},
    )
    assert response.status_code == 202
    data = response.json()
    assert data["status"] == "duplicate"
    assert data["run_id"] == "run-dup"


def test_intake_blocked_domain(monkeypatch):
    _set_env()
    os.environ["PREFILTER_BLOCKED_DOMAINS"] = "blocked.com"
    client = TestClient(app)

    payload = {
        "name": "Test User",
        "email": "test@blocked.com",
    }
    response = client.post(
        "/webhook/lead",
        json=payload,
        headers={"X-API-Key": "test-api-key"},
    )
    assert response.status_code == 202
    data = response.json()
    assert data["status"] == "filtered"
    assert data["reason"] == "blocked_domain"
