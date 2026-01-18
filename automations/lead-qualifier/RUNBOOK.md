# Lead Qualifier — Runbook

> **Purpose**: Deploy, monitor, and troubleshoot the lead qualifier automation.

---

## Quick Start

### Prerequisites

- [ ] Supabase project created
- [ ] OpenAI API key with GPT-4o access
- [ ] SendGrid account (for email sending)
- [ ] Slack webhook (for notifications)

### 1. Database Setup

```bash
# Run schema in Supabase SQL Editor
# Copy contents of schema.sql and execute
```

Verify tables exist:
- `leads`
- `runs`
- `outbox_emails`
- `email_history`
- `automation_status`
- `jobs_queue`
- `suppression_list`

### 2. Deploy API + Worker

```bash
# Create virtual environment
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac

# Install dependencies
pip install -r requirements.txt

# Create .env file
cp ../../.env.example .env
# Edit .env with your values

# Run FastAPI server (intake + admin + status)
uvicorn api.main:app --host 0.0.0.0 --port 8000

# Run worker (separate terminal/process)
python -m worker.main
```

### 3. (Optional) Import n8n Workflow

1. Open n8n
2. Create new workflow
3. Import → From File → Select `n8n-workflow.json`
4. Update credentials:
   - Supabase API credentials
   - Slack webhook URL
   - Environment variables (`DEFAULT_CLIENT_ID`)
5. Activate workflow

### 4. Test Webhook

```bash
curl -X POST https://your-api-host.com/webhook/lead \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Test User",
    "email": "test@example.com",
    "company": "Acme Corp",
    "message": "I need help automating my sales process",
    "source": "website"
  }'
```

Expected response (intake-only):
```json
{
  "status": "queued",
  "run_id": "...",
  "job_id": "...",
  "idempotency_key": "..."
}
```

---

## Monitoring

### Daily Checks

1. **Review LangSmith/Helicone**
   - Error rate < 5%
   - Average token cost per run
   - Latency trends

2. **Check Outbox Queue**
   ```sql
   SELECT * FROM outbox_emails 
   WHERE status = 'queued' 
   ORDER BY created_at DESC 
   LIMIT 20;
   ```

3. **Review Failed Runs**
   ```sql
   SELECT * FROM runs 
   WHERE status IN ('failed', 'killed') 
   AND started_at > NOW() - INTERVAL '24 hours'
   ORDER BY started_at DESC;
   ```

### Key Metrics

| Metric | Healthy | Warning | Critical |
|--------|---------|---------|----------|
| Error rate | < 2% | 2-5% | > 5% |
| Avg latency | < 10s | 10-30s | > 30s |
| Token cost/run | < $0.20 | $0.20-0.40 | > $0.40 |
| Queue depth | < 50 | 50-100 | > 100 |

### Alerts to Set Up

1. **Slack alert on failure**: Already in n8n workflow
2. **Daily summary**: Create scheduled n8n workflow
3. **Cost spike**: Monitor via LangSmith

---

## Troubleshooting

### Problem: Webhook returns 500

**Check**:
1. n8n execution log
2. Agent API endpoint responding?
3. Supabase credentials valid?

**Debug**:
```sql
-- Find latest run
SELECT * FROM runs ORDER BY started_at DESC LIMIT 1;

-- Check error
SELECT error_message, steps_json FROM runs WHERE id = 'RUN_ID';
```

### Problem: Agent timeout

**Cause**: LLM taking too long

**Fix**:
1. Check OpenAI status page
2. Increase timeout in n8n HTTP node
3. Check if prompt is too long

### Problem: Duplicate emails sent

**Check**: Idempotency and cooldown working?

```sql
-- Check if duplicate runs exist
SELECT idempotency_key, COUNT(*) 
FROM runs 
GROUP BY idempotency_key 
HAVING COUNT(*) > 1;

-- Check email history
SELECT * FROM email_history 
WHERE lead_email = 'user@example.com' 
ORDER BY sent_at DESC;
```

### Problem: Qualification scores seem wrong

**Debug**:
1. Check LangSmith trace for that run
2. Review the prompt sent to LLM
3. Look at enrichment data quality
4. Adjust rubric in `config.py`

### Problem: High token costs

**Check**:
```sql
SELECT 
  DATE(started_at) as day,
  SUM(llm_tokens_in + llm_tokens_out) as total_tokens,
  SUM(cost_estimate_usd) as total_cost,
  COUNT(*) as runs
FROM runs
WHERE started_at > NOW() - INTERVAL '7 days'
GROUP BY DATE(started_at)
ORDER BY day DESC;
```

**Fix**:
1. Check for long form messages being included
2. Review enrichment data size
3. Ensure MAX_TOKENS config is set

---

## Maintenance

### Weekly

- [ ] Review failed runs and add to failure catalog
- [ ] Approve/reject queued emails
- [ ] Check token costs vs budget

### Monthly

- [ ] Review qualification accuracy (spot check 10 random leads)
- [ ] Adjust rubric if needed
- [ ] Rotate API keys
- [ ] Review and update enrichment sources

### Quarterly

- [ ] Full audit of all automations
- [ ] Client feedback review
- [ ] Pricing adjustment if costs changed

---

## Emergency Procedures

### Pause Automation

**Option 1: Via n8n**
- Go to workflow → Toggle "Inactive"

**Option 2: Via Database**
```sql
UPDATE automation_status 
SET status = 'paused', paused_at = NOW(), pause_reason = 'Emergency pause'
WHERE automation_name = 'lead-qualifier';
```

### Resume Automation

```sql
UPDATE automation_status 
SET status = 'active', paused_at = NULL, pause_reason = NULL
WHERE automation_name = 'lead-qualifier';
```

Then reactivate n8n workflow.

### Emergency Rollback (Last 24 Hours)

```sql
-- Mark all recent runs as reversed
UPDATE runs 
SET status = 'reversed', error_message = 'Emergency rollback'
WHERE started_at > NOW() - INTERVAL '24 hours'
AND status = 'success';

-- Cancel all queued emails
UPDATE outbox_emails
SET status = 'rejected', rejected_reason = 'Emergency rollback'
WHERE status = 'queued'
AND created_at > NOW() - INTERVAL '24 hours';
```

---

## Scaling

### When to Scale

- Processing > 100 leads/day
- Latency > 15 seconds average
- Error rate increasing

### How to Scale

1. **Horizontal**: Run multiple n8n workers
2. **Vertical**: Upgrade Supabase tier
3. **Optimize**: 
   - Cache enrichment data
   - Batch similar leads
   - Use cheaper model for drafting

---

## Rollback to Previous Version

```bash
# Git rollback
git log --oneline -10  # Find previous commit
git checkout COMMIT_HASH -- automations/lead-qualifier/

# Redeploy agent
# Reimport n8n workflow (keep credentials)
```
