def handle(payload: dict) -> dict:
    invoice_status = payload.get("invoice_status", "pending")
    amount = payload.get("amount", "TBD")
    return {
        "status": "ok",
        "summary": "Finance ops review queued",
        "invoice_status": invoice_status,
        "amount": amount,
        "next_action": "process_invoice",
    }
