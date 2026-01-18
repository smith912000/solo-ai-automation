# Cursor Agent Work Packages

**Project**: `C:\Users\freez\.gemini\antigravity\scratch\solo-ai-automation`  
**Instructions**: Pick one task, read the context, complete it, then report results.

---

## Status Notes (Current)
- P0 smoke test: intake/worker verified with metrics.
- Slack alerts: code wired (`lib/slack.py`), delivery not verified.
- SendGrid: test email failed (403) — requires permission/domain fix.
- Outreach agent: stubs exist, API route removed from main.
- Lead enrichment: minimal domain-only.

## TASK 1: Smoke Test Verification
**Priority**: P0 (Blocker)  
**Estimated Time**: 30 min

### Context
Supabase credentials were just configured. Need to verify the full pipeline works.

### Steps
1. Start API: `uvicorn api.main:app --reload --port 8000`
2. Start Worker: `python -m worker.main`
3. Send test request:
```bash
curl -X POST http://localhost:8000/webhook/lead \
  -H "Content-Type: application/json" \
  -H "X-API-Key: solo-ai-automation-2026" \
  -d '{"name":"Test Lead","email":"test@example.com","company":"Acme Corp","message":"I need help with automations"}'
```
4. Check Supabase tables: `leads`, `runs`, `jobs_queue`

### Acceptance Criteria
- [ ] API returns 202 with `run_id` and `job_id`
- [ ] Worker claims and processes the job
- [ ] Lead appears in `leads` table
- [ ] Run record created in `runs` table
- [ ] Email draft appears in `outbox_emails`

### Files
- `api/routes/intake.py`
- `worker/main.py`
- `.env`

---

## TASK 2: Fix Route Imports
**Priority**: P0 (Blocker)  
**Estimated Time**: 30 min

### Context
Routes `outreach.py`, `onboarder.py`, `voice.py` import from automation agent folders that may have incomplete modules.

### Steps
1. Check if `api/main.py` starts without errors:
   ```python
   python -c "from api.main import app; print('OK')"
   ```
2. If import errors occur, for EACH broken route:
   - Option A: Complete the missing module with a working stub
   - Option B: Comment out the route in `api/main.py`

### Modules to Check
- `automations/outreach-agent/agent/cold_emailer.py` → needs `draft_cold_email()`
- `automations/client-onboarder/agent/main.py` → needs `ClientInfo`, `generate_checklist()`
- `automations/voice-agent/agent/main.py` → needs `place_call()`

### Acceptance Criteria
- [ ] `python -c "from api.main import app"` runs without errors
- [ ] `uvicorn api.main:app` starts successfully
- [ ] All existing endpoints still work

### Files
- `api/main.py`
- `api/routes/outreach.py`
- `api/routes/onboarder.py`
- `api/routes/voice.py`
- `automations/*/agent/`

---

## TASK 3: Configure SendGrid
**Priority**: P1  
**Estimated Time**: 1 hour

### Context
Email sending is stubbed but not functional. Need SendGrid integration.

### Steps
1. Review `lib/email.py` - understand current structure
2. Ensure SendGrid SDK is in `requirements.txt`: `sendgrid>=6.9.0`
3. Test with environment variables:
   - `SENDGRID_API_KEY` (from .env)
   - `SENDGRID_FROM_EMAIL`
   - `SENDGRID_FROM_NAME`
4. Create a test script to send one email
5. Wire into `worker/main.py` `send_approved_emails()` function

### Acceptance Criteria
- [ ] `lib/email.py` sends real email via SendGrid
- [ ] Test email received in inbox
- [ ] Worker can send approved emails from `outbox_emails`
- [ ] Error handling for SendGrid failures

### Files
- `lib/email.py`
- `worker/main.py`
- `requirements.txt`
- `.env`

---

## TASK 4: Wire Slack Alerts
**Priority**: P1  
**Estimated Time**: 1 hour

### Context
Slack webhook exists (`SLACK_WEBHOOK_URL` in .env) but isn't connected to the code.

### Steps
1. Create `lib/slack.py`:
   ```python
   def send_slack_alert(message: str, level: str = "info"):
       # POST to SLACK_WEBHOOK_URL
   ```
2. Add alerts for:
   - Worker errors (when job fails)
   - Kill switch triggered
   - High qualification score leads (score >= 80)
3. Test with sample messages

### Acceptance Criteria
- [ ] `lib/slack.py` exists with `send_slack_alert()`
- [ ] Worker sends Slack alert on job failure
- [ ] Kill switch logs to Slack
- [ ] High-score leads notify Slack
- [ ] Messages appear in #all-negotiorum

### Files
- `lib/slack.py` (create)
- `worker/main.py`
- `lib/kill_switch.py`

---

## TASK 5: Add Integration Tests
**Priority**: P2  
**Estimated Time**: 2 hours

### Context
Only 1 test file exists. Need comprehensive tests for client deployments.

### Steps
1. Create `tests/test_intake.py`:
   - Valid lead creates job
   - Duplicate detection works
   - Blocked domain filtered
2. Create `tests/test_worker.py`:
   - Job claiming works (mock Supabase)
   - Qualification flow (mock OpenAI)
3. Create `tests/test_admin.py`:
   - Metrics endpoint with API key
   - Outbox endpoints work

### Acceptance Criteria
- [ ] `pytest tests/` runs all tests
- [ ] At least 10 test cases total
- [ ] External APIs mocked (OpenAI, Supabase)
- [ ] All tests pass

### Files
- `tests/test_intake.py` (create)
- `tests/test_worker.py` (create)
- `tests/test_admin.py` (create)
- `tests/conftest.py` (create fixtures)

---

## TASK 6: Deploy to Railway
**Priority**: P2  
**Estimated Time**: 1 hour

### Context
Project has `railway.json` and `Dockerfile` but isn't deployed.

### Steps
1. Review `Dockerfile` - ensure it builds
2. Review `railway.json` - check start command
3. Test local Docker build: `docker build -t solo-ai .`
4. Create `Procfile` if needed: `web: uvicorn api.main:app --host 0.0.0.0 --port $PORT`
5. Update `README.md` with deployment instructions
6. Worker needs separate service config

### Acceptance Criteria
- [ ] `docker build` succeeds locally
- [ ] `docker run` starts API
- [ ] README has Railway deployment steps
- [ ] Worker deployment documented

### Files
- `Dockerfile`
- `railway.json`
- `Procfile` (create if needed)
- `README.md`

---

## TASK 7: Complete Outreach Agent
**Priority**: P3  
**Estimated Time**: 4 hours

### Context
Outreach agent has stubs but isn't functional. Enables AI prospecting.

### Steps
1. Complete `automations/outreach-agent/agent/cold_emailer.py`:
   - Use OpenAI to draft cold emails
   - Accept: name, role, company, website, pain_points, notes
   - Return: subject, body, follow_up_task, tokens_in, tokens_out, model_name
2. Add config in `automations/outreach-agent/agent/config.py`
3. Test via `/outreach/draft` endpoint

### Acceptance Criteria
- [ ] `POST /outreach/draft` returns email draft
- [ ] Email is personalized to input
- [ ] Token usage tracked
- [ ] Reasonable prompt engineering

### Files
- `automations/outreach-agent/agent/cold_emailer.py`
- `automations/outreach-agent/agent/config.py`
- `api/routes/outreach.py`

---

## TASK 8: Improve Lead Enrichment
**Priority**: P3  
**Estimated Time**: 2 hours

### Context
Current enrichment just scrapes website titles. Need better data.

### Steps
1. Review `lib/enrichment.py`
2. Add Clearbit or Apollo integration (if API keys available)
3. Or improve scraping: meta description, LinkedIn, company size estimates
4. Cache enrichment results to avoid duplicate calls

### Acceptance Criteria
- [ ] Enrichment returns: industry, size, description
- [ ] Works for most company websites
- [ ] Caching prevents duplicate API calls
- [ ] Graceful fallback if enrichment fails

### Files
- `lib/enrichment.py`
- `.env` (add API keys if needed)

---

## Agent Assignment Recommendations

| Task | Best For | Reason |
|------|----------|--------|
| 1. Smoke Test | Any agent | Tests the system |
| 2. Fix Routes | Backend agent | Import/module fixes |
| 3. SendGrid | Backend agent | API integration |
| 4. Slack Alerts | Backend agent | Simple integration |
| 5. Tests | Testing agent | pytest knowledge |
| 6. Deploy | DevOps agent | Docker/Railway |
| 7. Outreach | AI agent | Prompt engineering |
| 8. Enrichment | Backend agent | Web scraping/APIs |
