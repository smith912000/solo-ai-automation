"""
Route non-lead-qualifier jobs to agency role handlers.
"""

from __future__ import annotations

import importlib
import importlib.machinery
import importlib.util
import os
import sys
import time
from typing import Callable

from supabase import Client

from lib import db as db_lib

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
AGENCY_ROOT = os.path.join(ROOT_DIR, "automations", "agency-ops")
AGENCY_AGENT_DIR = os.path.join(AGENCY_ROOT, "agent")


def _load_agent_module(package_name: str, package_path: str, module_name: str):
    if package_name not in sys.modules:
        package = importlib.util.module_from_spec(
            importlib.machinery.ModuleSpec(package_name, None)
        )
        package.__path__ = [package_path]
        sys.modules[package_name] = package
    return importlib.import_module(f"{package_name}.{module_name}")


_agency_sales = _load_agent_module("agency_ops", AGENCY_AGENT_DIR, "sales")
_agency_ops = _load_agent_module("agency_ops", AGENCY_AGENT_DIR, "ops")
_agency_support = _load_agent_module("agency_ops", AGENCY_AGENT_DIR, "support")
_agency_growth = _load_agent_module("agency_ops", AGENCY_AGENT_DIR, "growth")
_agency_account = _load_agent_module("agency_ops", AGENCY_AGENT_DIR, "account_manager")
_agency_proposal = _load_agent_module("agency_ops", AGENCY_AGENT_DIR, "proposal_builder")
_agency_delivery = _load_agent_module("agency_ops", AGENCY_AGENT_DIR, "delivery_planner")
_agency_success = _load_agent_module("agency_ops", AGENCY_AGENT_DIR, "client_success")
_agency_finance = _load_agent_module("agency_ops", AGENCY_AGENT_DIR, "finance_ops")
_agency_qa = _load_agent_module("agency_ops", AGENCY_AGENT_DIR, "qa_review")


ROUTES: dict[str, Callable[[dict], dict]] = {
    "sales_outreach": _agency_sales.handle,
    "sales_followup": _agency_sales.handle,
    "ops_task": _agency_ops.handle,
    "support_reply": _agency_support.handle,
    "growth_experiment": _agency_growth.handle,
    "account_manager": _agency_account.handle,
    "proposal_builder": _agency_proposal.handle,
    "delivery_planner": _agency_delivery.handle,
    "client_success": _agency_success.handle,
    "finance_ops": _agency_finance.handle,
    "qa_review": _agency_qa.handle,
}


def route_job(db: Client, job: dict) -> dict:
    job_type = job.get("job_type") or "sales_outreach"
    payload = job.get("payload") or {}
    client_id = job.get("client_id")
    correlation_id = job.get("correlation_id")
    priority = job.get("priority", 0)

    handler = ROUTES.get(job_type, _agency_sales.handle)
    task = db_lib.create_agent_task(
        db,
        client_id=client_id,
        task_type=job_type,
        payload=payload,
        priority=priority,
        assigned_agent=handler.__module__.split(".")[-1],
        correlation_id=correlation_id,
    )

    start_time = time.time()
    try:
        result = handler(payload)
        duration_ms = int((time.time() - start_time) * 1000)
        db_lib.record_agent_run(
            db,
            client_id=client_id,
            task_id=task.get("id"),
            agent_name=handler.__module__.split(".")[-1],
            status="success",
            input_json=payload,
            output_json=result,
            duration_ms=duration_ms,
        )
        db_lib.update_agent_task_status(db, task.get("id"), "done")
        return result
    except Exception as exc:
        duration_ms = int((time.time() - start_time) * 1000)
        db_lib.record_agent_run(
            db,
            client_id=client_id,
            task_id=task.get("id"),
            agent_name=handler.__module__.split(".")[-1],
            status="failed",
            input_json=payload,
            error_message=str(exc),
            duration_ms=duration_ms,
        )
        db_lib.update_agent_task_status(db, task.get("id"), "failed")
        raise
