# Daily Workflow

> How you spend your time as a solo AI automation operator.

---

## Morning Block (1-2 hours)

### 1. System Health Check (15 min)

```
Morning checklist:
□ Check LangSmith/Helicone for overnight errors
□ Review Slack alerts (if any)
□ Check n8n execution logs
□ Verify all automations are active
```

**SQL quick checks:**

```sql
-- Failed runs in last 24h
SELECT automation_name, COUNT(*), MAX(error_message)
FROM runs 
WHERE status IN ('failed', 'killed')
AND started_at > NOW() - INTERVAL '24 hours'
GROUP BY automation_name;

-- Cost by client
SELECT client_id, SUM(cost_estimate_usd) as daily_cost
FROM runs
WHERE started_at > NOW() - INTERVAL '24 hours'
GROUP BY client_id;
```

### 2. Approval Queue (15-30 min)

Review and approve/reject queued emails:

```sql
-- Pending approvals
SELECT id, to_email, subject, created_at
FROM outbox_emails
WHERE status = 'queued'
ORDER BY created_at ASC;
```

For each email:
- [ ] Subject line appropriate?
- [ ] Body personalized correctly?
- [ ] CTA clear?
- [ ] No weird AI artifacts?

### 3. Client Communication (30 min)

- [ ] Respond to any support requests
- [ ] Send daily summaries (if applicable)
- [ ] Check for urgent escalations

---

## Midday Block (3-4 hours)

### 4. Build/Fix Time (2-3 hours)

**This is your deep work block.** No Slack, no email.

Possible activities:
- Building new automation features
- Fixing bugs from morning health check
- Optimizing existing automations
- Documenting patterns in failure catalog

**Use Cursor effectively:**
- Start with `Cmd+K` to explain what you want
- Let the agent draft, you review
- Commit after each working chunk

### 5. Testing (30-60 min)

- Run tests on any code changes
- Test with sample data before deploying
- Update runbooks if behavior changed

---

## Afternoon Block (2-3 hours)

### 6. Sales & Marketing (1-2 hours)

**Use your own automations for this.**

Activities:
- [ ] LinkedIn prospecting (manual or automated)
- [ ] Follow up on discovery calls
- [ ] Content creation (if applicable)
- [ ] Outreach to new leads

**Track in your own CRM:**
- Leads in pipeline
- Discovery calls scheduled
- Proposals sent
- Contracts pending

### 7. Client Meetings (as scheduled)

- Discovery calls (15-30 min)
- Onboarding sessions (30-60 min)
- Monthly reviews (30 min)

**Prep before each call:**
- Review their usage data
- Check any open issues
- Prepare expansion ideas

---

## Evening Block (30-60 min)

### 8. Documentation (15-30 min)

- [ ] Update failure catalog with any new patterns
- [ ] Document any workarounds used today
- [ ] Update runbooks if needed
- [ ] Let Cursor help with docs (`@docs` feature)

### 9. Planning (15-30 min)

- [ ] Review tomorrow's calendar
- [ ] Set 1-3 priorities for tomorrow
- [ ] Note any blockers to address
- [ ] Update task.md with progress

---

## Weekly Additions

### Monday

- [ ] Client usage summaries (automated where possible)
- [ ] Week planning

### Wednesday

- [ ] Midweek pipeline review
- [ ] Follow up on pending proposals

### Friday

- [ ] Week in review (what worked, what didn't)
- [ ] Failure catalog review
- [ ] Prepare for next week

---

## Key Principles

### 1. Protect Deep Work

- Morning health check = mechanical, don't overthink
- Midday build time = protected, no interruptions
- Batch communications, don't react all day

### 2. Automate Your Own Work

If you do something 3+ times:
- Can an agent do it?
- Can a workflow do it?
- Can at least a template do it?

### 3. Energy Management

- Complex problems → morning/midday
- Admin/email → afternoon
- Planning → evening
- Never build when tired

### 4. Document Everything

Future you will thank present you.

---

## Time Allocation (Target)

| Activity | Hours/Week |
|----------|------------|
| Health checks | 5 |
| Approval queues | 3 |
| Client support | 5 |
| Building/fixing | 15 |
| Sales/marketing | 7 |
| Meetings | 3 |
| Documentation | 2 |
| **Total** | **40** |

Adjust based on:
- Client count
- Automation complexity
- Sales pipeline stage
