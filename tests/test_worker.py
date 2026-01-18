import os
from types import SimpleNamespace

from lib import db as db_lib
from worker import main as worker


def _set_env():
    os.environ["DEFAULT_CLIENT_ID"] = "00000000-0000-0000-0000-000000000001"
    os.environ["EMAIL_COOLDOWN_DAYS"] = "7"
    os.environ["MAX_COST_PER_RUN_USD"] = "0.50"


def test_job_claiming(monkeypatch):
    _set_env()
    calls = {"done": False}

    monkeypatch.setattr(db_lib, "get_supabase_client", lambda: object())
    monkeypatch.setattr(
        db_lib,
        "claim_next_job",
        lambda *_: {"id": "job-1", "attempts": 0, "payload": {"email": "a@b.com"}, "client_id": "c1"},
    )
    monkeypatch.setattr(worker, "process_job", lambda *_: None)
    monkeypatch.setattr(db_lib, "mark_job_done", lambda *_: calls.update(done=True))

    ran = worker.run_once()
    assert ran is True
    assert calls["done"] is True


def test_lead_qualification_flow(monkeypatch):
    _set_env()

    monkeypatch.setattr(db_lib, "get_supabase_client", lambda: object())
    monkeypatch.setattr(db_lib, "upsert_lead", lambda *_: None)
    monkeypatch.setattr(db_lib, "get_automation_status", lambda *_: {"status": "active"})
    monkeypatch.setattr(db_lib, "is_email_suppressed", lambda *_: False)
    monkeypatch.setattr(db_lib, "email_sent_recently", lambda *_: False)
    monkeypatch.setattr(db_lib, "update_run_details", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(db_lib, "update_lead_qualification", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(db_lib, "queue_email", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(db_lib, "record_email_sent", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(db_lib, "update_lead_status", lambda *_args, **_kwargs: None)

    fake_qual = SimpleNamespace(
        score=80,
        label="qualified",
        key_reason="Good fit",
        personalization_points=["Point 1"],
        tokens_used=100,
        tokens_in=60,
        tokens_out=40,
        model_name="gpt-4o",
    )
    fake_draft = SimpleNamespace(
        subject="Hello",
        body="Hi there",
        tokens_used=80,
        tokens_in=40,
        tokens_out=40,
        model_name="gpt-4o-mini",
    )
    monkeypatch.setattr(worker, "qualify_lead", lambda **_kwargs: fake_qual)
    monkeypatch.setattr(worker, "draft_email", lambda **_kwargs: fake_draft)
    monkeypatch.setattr(worker, "enrich_company", lambda *_: {"domain": "example.com"})

    payload = {
        "name": "Test User",
        "email": "test@example.com",
        "company": "Acme",
        "message": "Hello",
    }
    result = worker.process_payload(
        client_id="c1",
        payload=payload,
        run_id="run-1",
        idempotency_key="idem-1",
        approval_mode_override=True,
    )
    assert result["status"] == "success"
    assert result["email_status"] == "queued"


def test_email_drafting_mock(monkeypatch):
    _set_env()

    fake_draft = SimpleNamespace(
        subject="Hello",
        body="Hi there",
        tokens_used=10,
        tokens_in=5,
        tokens_out=5,
        model_name="gpt-4o-mini",
    )
    monkeypatch.setattr(worker, "draft_email", lambda **_kwargs: fake_draft)
    draft = worker.draft_email(
        name="Test",
        company="Acme",
        message="Hello",
        qualification=SimpleNamespace(
            score=80,
            key_reason="Good fit",
            personalization_points=["Point 1"],
        ),
        enrichment_data={},
    )
    assert draft.subject == "Hello"
