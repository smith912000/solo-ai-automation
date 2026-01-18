# Ceiling Limits

> A solo AI business fails not from lack of capability but from exceeding sustainable complexity.

These are **non-negotiable constraints**. Violating them leads to burnout, unreliability, or collapse.

---

## Agent Limits

| Constraint | Maximum | Rationale |
|------------|---------|-----------|
| Agents per workflow | 5 | More = debugging nightmare |
| LLM calls per execution | 15 | Cost control + latency |
| Retries per step | 2 | Fail fast, don't loop forever |
| Execution time | 5 minutes | If it takes longer, it's broken |
| Token budget per run | 5,000 | Prevents runaway costs |

### The 5-Minute Whiteboard Rule

> If you can't explain the automation on a whiteboard in 5 minutes, it's too complex to sell or maintain solo.

---

## Client Limits

| Constraint | Maximum | Rationale |
|------------|---------|-----------|
| Concurrent clients | 10-15 | Support bandwidth |
| Automations per client | 3-5 | Complexity ceiling |
| New clients per month | 2-3 | Onboarding capacity |
| Custom requests per client | 2 | Maintain template discipline |

### What happens when you hit limits

1. **Raise prices** — Higher price = fewer clients for same revenue
2. **Fire lowest-value clients** — Ruthlessly
3. **Templatize harder** — Make customization configurable, not coded
4. **Consider first hire** — But not before 10 stable clients

---

## Cost Limits

| Constraint | Maximum | Rationale |
|------------|---------|-----------|
| LLM cost per run | $0.50 | Margin protection |
| Monthly LLM spend per client | $50 | Pricing sanity |
| API calls to external services | 10 per run | Rate limit respect |

### Token budget breakdown (example)

For a lead qualification + email draft:

| Step | Tokens (approx) |
|------|-----------------|
| Enrichment summary | 500 |
| Qualification reasoning | 1,500 |
| Email draft | 1,000 |
| Buffer | 2,000 |
| **Total** | 5,000 |

At GPT-4 rates (~$0.03/1k tokens): **$0.15 per lead**

---

## Complexity Ceiling by Automation Type

| Type | Max Steps | Max Agents | OK to Build Solo? |
|------|-----------|------------|-------------------|
| Simple trigger → action | 3 | 1 | ✅ Always |
| Multi-step with branching | 5 | 2 | ✅ Yes |
| Loop with human-in-loop | 7 | 3 | ⚠️ Careful |
| Multi-agent orchestration | 10+ | 4+ | ❌ Team required |

---

## When to Say No

Decline the project if:

- [ ] Client wants "AI that runs the whole business"
- [ ] No clear input/output definition
- [ ] Success criteria are subjective
- [ ] Expected to work on data you can't access
- [ ] Timeline is "ASAP" with no scope
- [ ] Pricing discussion involves "equity" instead of cash

---

## The Constraint Optimizer

You have exactly 3 bottlenecks as a solo operator:

### 1. Attention
You can only focus on one complex problem at a time.

**Mitigation**: 
- Deep work blocks (no Slack)
- One major build per day
- Batch similar tasks

### 2. Trust
Clients need to believe the automation won't break.

**Mitigation**:
- Approval mode first
- Gradual rollout (10% → 50% → 100%)
- Clear SLAs with escape hatches

### 3. Recovery Time
When something fails at 3am.

**Mitigation**:
- Circuit breakers
- Automatic pause on anomalies
- "Business hours only" SLA

---

## Enforcement

These limits must be:

1. **Documented** — Client sees them in contract
2. **Configured** — Hard-coded in agent config
3. **Monitored** — Alerts when approaching limits
4. **Respected** — No exceptions, even for "quick favors"

```python
# Example hard limits in config.py
MAX_AGENTS_PER_WORKFLOW = 5
MAX_LLM_CALLS_PER_RUN = 15
MAX_RETRIES_PER_STEP = 2
MAX_EXECUTION_TIME_SECONDS = 300
MAX_TOKENS_PER_RUN = 5000
```
