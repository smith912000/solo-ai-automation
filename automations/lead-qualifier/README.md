# Lead Qualifier Automation

> **Product Name**: Website Lead Autopilot  
> **SLA**: 99% of leads processed within 2 minutes

---

## What It Does

```
Website Form → Qualify → Enrich → Personalized Email → CRM
     ↓           ↓         ↓            ↓              ↓
  Webhook    Score 0-100  Company   Draft + Send    Lead Record
             + Reason     Data      or Queue        + Run Log
```

---

## Trigger

**Type**: Webhook (POST)  
**Endpoint**: `https://your-api-host.com/webhook/lead`
**Auth**: `X-API-Key` header (value = `API_KEY` in `.env`)

**Note**: n8n is optional and should be used only for downstream connector actions.

---

## Input Schema

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | string | ✅ | Contact name |
| `email` | string | ✅ | Contact email |
| `company` | string | ⚠️ | Company name |
| `website` | string | ⚠️ | Company website |
| `message` | string | ⚠️ | Form message/inquiry |
| `source` | string | ⚠️ | Where they came from |
| `timestamp` | string | ⚠️ | ISO timestamp |

**Minimum viable**: `name` + `email`

---

## Output Schema

### Qualification Result

```json
{
  "qualification_score": 75,
  "qualification_label": "qualified",
  "key_reason": "Mid-size SaaS company actively looking for automation",
  "personalization_points": [
    "Mentioned scaling pain in their message",
    "Company raised Series A recently"
  ],
  "email_subject": "Quick question about your automation needs",
  "email_body": "Hi [Name]...",
  "follow_up_task": "Schedule demo if no response in 3 days"
}
```

### Labels

| Label | Score Range | Action |
|-------|-------------|--------|
| `qualified` | 70-100 | Send email (or queue) |
| `review` | 40-69 | Queue for manual review |
| `disqualified` | 0-39 | Log only, no action |

---

## Workflow Steps

### 1. Receive Webhook
- Validate required fields (name, email)
- Compute idempotency key: `hash(email + timestamp + source)`
- Check if key exists in `runs` table → exit if duplicate

### 2. Upsert Lead
- Insert or update lead by email
- Store raw form data

### 3. Enrich (Optional)
- Scrape company website OR call enrichment API
- Extract: industry, size, recent news, tech stack
- If enrichment fails → continue with available data

### 4. Qualify + Draft
- Call agent with form data + enrichment
- Agent returns structured JSON
- Validate output schema

### 5. Route by Score
- **Qualified (70+)**: Send email OR queue for approval
- **Review (40-69)**: Queue for manual review
- **Disqualified (0-39)**: Log and exit

### 6. Send/Queue Email
- If `APPROVAL_MODE=true`: Insert to `outbox_emails`
- If `APPROVAL_MODE=false`: Send via SendGrid
- Check "sent within X days" guard first
 - Use `POST /admin/outbox/{outbox_id}/approve|reject|send` for manual control

### 7. Log Run
- Record all steps, tokens, costs, errors
- Store decision path for debugging

### 8. Notify
- Slack message with summary
- Include links to lead record and run log

### 9. Operations Controls
- Pause/resume automation with `POST /admin/automation/lead-qualifier/pause|resume`

---

## Kill Conditions

Halt immediately if:

| Condition | Detection |
|-----------|-----------|
| Duplicate run | Idempotency key exists |
| Token spike | > 5,000 tokens |
| Loop detected | Same step > 2x |
| Email already sent | Within last 7 days |
| Invalid agent output | JSON parse fails |

---

## Configuration

See `agent/config.py` for:
- Model selection
- Token limits
- Prompt templates
- Scoring rubric

---

## Files

| File | Purpose |
|------|---------|
| `schema.sql` | Supabase table definitions |
| `n8n-workflow.json` | Importable n8n workflow |
| `agent/config.py` | Models, limits, prompts |
| `agent/qualifier.py` | Lead scoring logic |
| `agent/email_drafter.py` | Email personalization |
| `agent/main.py` | Entry point + kill switches |
| `RUNBOOK.md` | Deploy, monitor, troubleshoot |

---

## Pricing This Automation

### Cost per lead (estimated)

| Component | Cost |
|-----------|------|
| LLM (qualification + draft) | $0.10-0.20 |
| Enrichment API | $0.05-0.10 |
| Email sending | ~$0.001 |
| **Total** | **$0.15-0.30** |

### Suggested pricing

| Model | Price |
|-------|-------|
| Per lead | $1-2 |
| Monthly flat | $500-1,000 (up to 500 leads) |

### Margin
At $1/lead, margin is 70-85%.
