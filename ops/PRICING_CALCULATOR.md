# Pricing Calculator

> Calculate your costs and set profitable pricing.

---

## Token Cost Reference

### Model Pricing (per 1M tokens, as of 2024)

| Model | Input | Output |
|-------|-------|--------|
| GPT-4o | $5.00 | $15.00 |
| GPT-4o-mini | $0.15 | $0.60 |
| GPT-4-turbo | $10.00 | $30.00 |
| Claude 3.5 Sonnet | $3.00 | $15.00 |
| Claude 3 Haiku | $0.25 | $1.25 |

### Typical Lead Qualifier Usage

| Step | Input Tokens | Output Tokens |
|------|--------------|---------------|
| Qualification | ~1,000 | ~500 |
| Email Draft | ~800 | ~400 |
| **Total** | **~1,800** | **~900** |

---

## Cost per Lead Calculator

### Using GPT-4o (high quality)

```
Input cost:  1,800 tokens × ($5.00 / 1M) = $0.009
Output cost:   900 tokens × ($15.00 / 1M) = $0.0135
─────────────────────────────────────────────────
LLM Total: $0.0225 per lead
```

### Using GPT-4o-mini (budget)

```
Input cost:  1,800 tokens × ($0.15 / 1M) = $0.00027
Output cost:   900 tokens × ($0.60 / 1M) = $0.00054
─────────────────────────────────────────────────
LLM Total: $0.00081 per lead (< 1 cent!)
```

### Hybrid Approach (recommended)

| Step | Model | Cost |
|------|-------|------|
| Qualification | GPT-4o | $0.02 |
| Email Draft | GPT-4o-mini | $0.001 |
| **Total** | | **$0.021** |

---

## Full Cost Stack

### Per-Lead Costs

| Component | Cost | Notes |
|-----------|------|-------|
| LLM calls | $0.02-0.15 | Depends on model |
| Enrichment API | $0.00-0.10 | If using Clearbit, etc. |
| Email sending | $0.001 | SendGrid pricing |
| Database storage | ~$0.0001 | Negligible |
| **Total** | **$0.02-0.26** | |

### Fixed Monthly Costs

| Component | Cost | Notes |
|-----------|------|-------|
| n8n (self-hosted) | $5-10 | Railway/Fly.io |
| Supabase | $0-25 | Free tier often enough |
| SendGrid | $0-15 | Free tier for low volume |
| LangSmith | $0-39 | Free tier available |
| **Total** | **$5-90** | |

---

## Pricing Tiers

### Starter: $500/month

| Metric | Value |
|--------|-------|
| Leads included | 200 |
| Cost per lead | $0.15 |
| Your variable cost | $30 |
| Your fixed cost | $25 |
| **Gross profit** | **$445 (89%)** |

### Growth: $1,000/month

| Metric | Value |
|--------|-------|
| Leads included | 500 |
| Cost per lead | $0.15 |
| Your variable cost | $75 |
| Your fixed cost | $25 |
| **Gross profit** | **$900 (90%)** |

### Pro: $2,000/month

| Metric | Value |
|--------|-------|
| Leads included | Unlimited (est. 1,500) |
| Cost per lead | $0.10 (volume efficiencies) |
| Your variable cost | $150 |
| Your fixed cost | $50 |
| **Gross profit** | **$1,800 (90%)** |

---

## Break-Even Analysis

### Monthly Fixed Costs

| Item | Monthly |
|------|---------|
| Infrastructure | $50 |
| Software subscriptions | $100 |
| Your time (opportunity cost) | $5,000 |
| **Total** | **$5,150** |

### Clients Needed to Break Even

| Tier | Revenue | Clients Needed |
|------|---------|----------------|
| Starter ($500) | $500/client | 11 clients |
| Growth ($1,000) | $1,000/client | 6 clients |
| Pro ($2,000) | $2,000/client | 3 clients |

**Recommended mix:** 2 Pro + 3 Growth = $7,000/month

---

## Value-Based Pricing Check

### Calculate Client Value

| Factor | Example |
|--------|---------|
| Hours saved/week | 10 hours |
| Hourly rate (employee) | $50/hour |
| Weekly savings | $500 |
| Monthly savings | $2,000 |
| Annual savings | $24,000 |

### The 10x Rule

Your price should be ~10% of their savings.

```
Client saves: $24,000/year
You charge:   $2,400/year ($200/month)
ROI for client: 10x return
```

### Pricing Sweet Spot

- **Too cheap (<5%):** Client doesn't value it, you undersell
- **Sweet spot (10-20%):** Clear ROI, easy yes
- **Expensive (>30%):** Needs more justification

---

## Per-Lead Pricing Model

Alternative to monthly subscription:

| Tier | Per Lead | Minimum |
|------|----------|---------|
| Starter | $2.00 | 100 leads/month ($200) |
| Growth | $1.50 | 300 leads/month ($450) |
| Pro | $1.00 | Unlimited |

### When to Use Per-Lead

✅ Client has variable lead volume
✅ Testing before commitment
✅ High-ticket leads (consulting, enterprise)

### When to Avoid

❌ Low volume = low revenue
❌ Client wants predictable costs
❌ You want predictable income

---

## Margin by Client Type

### High Margin (Target)

| Type | Characteristics |
|------|-----------------|
| SaaS companies | High LTV leads, can afford premium |
| Agencies | Bundle with other services |
| Professional services | High-ticket outcomes |

### Lower Margin (Avoid Unless Volume)

| Type | Issue |
|------|-------|
| E-commerce | Very high volume, low per-lead value |
| Startups (pre-revenue) | Can't afford, high support |
| Enterprises | Long sales cycle, custom needs |

---

## Quick Calculator

### Input Your Numbers

```
Leads per month:     _____
Cost per lead:       $_____
Your monthly price:  $_____
Fixed costs:         $_____

Variable costs = Leads × Cost per lead = _____
Gross profit = Price - Variable - Fixed = _____
Margin % = Gross profit / Price = _____
```

### Example

```
Leads per month:     300
Cost per lead:       $0.15
Your monthly price:  $1,000
Fixed costs:         $50

Variable costs = 300 × $0.15 = $45
Gross profit = $1,000 - $45 - $50 = $905
Margin % = $905 / $1,000 = 90.5%
```

---

## Pricing Rules

1. **Price on value, not cost** — If they save $2k/month, charge $500
2. **Round up, not down** — $500 feels same as $450, captures more
3. **Annual discount = 15-20%** — Lock in cash, reduce churn
4. **Never compete on price** — Let cheap clients go elsewhere
5. **Raise prices as you learn** — Each client teaches you more
