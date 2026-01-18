# Failure Catalog

> Treat failures as assets, not bugs. Every failure logged becomes part of your moat.

---

## Why This Exists

Your actual competitive advantage is:
- **Accumulated, documented failure knowledge**
- **Proven rollback patterns**

Not prompt engineering. Not tool choice.

---

## How to Use This

1. When a failure occurs, copy the template below
2. Fill in all fields
3. Document the resolution
4. Add to patterns library if novel

---

## Failure Entry Template

```markdown
## [DATE] - [SHORT TITLE]

### Category
<!-- One of: API_FAILURE, EDGE_CASE, PROMPT_FAILURE, COST_OVERRUN, DATA_ANOMALY, INTEGRATION_BREAK -->

### Severity
<!-- CRITICAL / HIGH / MEDIUM / LOW -->

### Automation
<!-- Which automation + client -->

### Symptoms
<!-- What did you observe? Error messages? -->

### Root Cause
<!-- Why did this actually happen? -->

### Resolution
<!-- What fixed it? -->

### Prevention
<!-- How do we prevent this class of failure? -->

### Tags
<!-- Keywords for searchability -->
```

---

## Failure Categories

### API_FAILURE
External service returned error or timeout.

**Common examples**:
- Rate limit hit
- Authentication expired
- Service outage
- Unexpected response format

**Standard mitigations**:
- Exponential backoff
- Fallback provider
- Graceful degradation

---

### EDGE_CASE
Input that the automation didn't handle.

**Common examples**:
- Missing required field
- Unexpected data format
- Unicode/encoding issues
- Extremely long input

**Standard mitigations**:
- Input validation
- Truncation with notice
- Default values

---

### PROMPT_FAILURE
LLM returned unexpected/invalid output.

**Common examples**:
- Invalid JSON
- Hallucinated fields
- Refusal to respond
- Off-topic response

**Standard mitigations**:
- Structured output mode
- Retry with rephrased prompt
- Fallback to simpler prompt
- Manual review queue

---

### COST_OVERRUN
Token usage exceeded budget.

**Common examples**:
- Prompt too long
- Loop didn't terminate
- Retry storm
- Context window overflow

**Standard mitigations**:
- Token limits in config
- Kill switch on threshold
- Chunked processing

---

### DATA_ANOMALY
Data didn't match expectations.

**Common examples**:
- Duplicate records
- Stale data
- Cross-client data leak
- Schema migration issue

**Standard mitigations**:
- Idempotency keys
- Data validation layer
- Client isolation

---

### INTEGRATION_BREAK
Third-party changed their system.

**Common examples**:
- API deprecation
- New required field
- Rate limit policy change
- OAuth scope change

**Standard mitigations**:
- Version pinning
- Integration health checks
- Vendor changelog monitoring

---

## Pattern Library

Document recurring failure patterns and their solutions here.

### Pattern: Email Already Sent

**Problem**: Duplicate webhook fired, sent customer duplicate email.

**Solution**: 
- Idempotency key on webhook (hash of email + timestamp)
- "Sent within X days" check before sending

---

### Pattern: Enrichment API Down

**Problem**: Lead enrichment fails, blocking entire pipeline.

**Solution**:
- Route to "needs_review" status
- Continue with available data
- Alert for manual enrichment

---

### Pattern: LLM Returns Invalid JSON

**Problem**: Agent output can't be parsed.

**Solution**:
- Use structured output mode (OpenAI) or XML tags (Claude)
- Retry once with "respond ONLY with JSON"
- Log the raw output for debugging

---

### Pattern: Token Explosion

**Problem**: Long email thread caused 10x normal token usage.

**Solution**:
- Truncate context to last N messages
- Summarize historical context
- Hard cap with truncation + notice

---

## Logged Failures

<!-- Add entries below as they occur -->

### [Template - Delete This]

## 2024-01-15 - Example Failure

### Category
API_FAILURE

### Severity
MEDIUM

### Automation
lead-qualifier / client: Acme Corp

### Symptoms
SendGrid returned 429 Too Many Requests at 2:47am

### Root Cause
Daily sending limit hit (100 free tier)

### Resolution
Upgraded to paid SendGrid tier

### Prevention
- Monitor daily send count
- Alert at 80% of limit
- Queue excess for next day

### Tags
sendgrid, rate-limit, email
