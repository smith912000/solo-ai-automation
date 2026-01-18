# Tech Stack

> Every tool choice is a tradeoff. This documents why we chose what we chose.

---

## The Stack at a Glance

| Layer | Tool | Why |
|-------|------|-----|
| **Control Tower** | Cursor + Claude | You're already here. Best agent-assisted coding. |
| **Agent Runtime** | Python + LangGraph | Composable, debuggable, production-ready. |
| **Integration Hub** | n8n (self-hosted) | Visual debugging, webhooks, retries. Cheaper than Zapier. |
| **Memory** | Supabase | Postgres + vectors + auth in one. Free tier is generous. |
| **Observability** | LangSmith | See token costs + trace every LLM call. |
| **Secrets** | Doppler or .env | Never commit API keys. |
| **Email** | SendGrid | Deliverability matters. Gmail for MVP only. |
| **Notifications** | Slack | Where you already live. |

---

## Layer-by-Layer Decisions

### 1. Control Tower: Cursor + Claude

**What it does**: Your IDE where agents build code for you.

**Why Cursor**:
- Multi-file reasoning
- Inline agent execution
- Git integration
- You're supervising, not typing

**Model choice**:
- Claude for reasoning/planning (more coherent)
- GPT-4 for execution/iteration (faster, cheaper)
- Keep both available to avoid vendor lock-in

---

### 2. Agent Runtime: Python + LangGraph

**What it does**: Runs your actual automation logic.

**Why Python**:
- Best LLM library ecosystem
- Easy to deploy anywhere
- You can debug it

**Why LangGraph** (over CrewAI, AutoGPT, etc.):
- State machines, not prompt chaining
- Explicit control flow
- Built-in retries and branching
- Production-ready (used by real companies)

**Alternatives considered**:
| Tool | Verdict |
|------|---------|
| CrewAI | Too "magic" — hard to debug |
| AutoGPT | Unstable for production |
| Raw API calls | Fine for simple cases |
| Custom orchestration | LangGraph is this, but better |

---

### 3. Integration Hub: n8n (Self-Hosted)

**What it does**: Connects everything. Receives webhooks. Calls APIs. Retries failures.

**Why n8n**:
- Visual workflow editor
- Self-hosted = no per-execution costs
- Built-in error handling
- 400+ integrations
- Can call your Python agent as HTTP endpoint

**Why NOT Zapier/Make**:
| Issue | Zapier/Make | n8n |
|-------|-------------|-----|
| Cost at scale | $399+/month | $0 (self-hosted) |
| Complex logic | Painful | Native code nodes |
| Debugging | Black box | Full logs |
| Rate limiting | Their limits | Your limits |

**Deployment**:
- Railway ($5/month)
- Fly.io (free tier works)
- Your own VPS

---

### 4. Memory: Supabase

**What it does**: Stores leads, runs, emails, everything.

**Why Supabase**:
- Postgres (real database, not a toy)
- Vector extension (pgvector) for semantic search
- Auth built-in (if you need client portals)
- Generous free tier
- Dashboard for quick checks

**Tables you'll need**:
- `leads` — your prospects
- `runs` — automation execution logs
- `outbox_emails` — approval queue

---

### 5. Observability: LangSmith

**What it does**: Shows you what your LLMs are doing and costing.

**Why LangSmith**:
- Trace every LLM call
- See token counts + costs
- Debug failed runs
- Compare prompts

**Alternatives**:
| Tool | Verdict |
|------|---------|
| Helicone | Good, but less LangChain-native |
| Langfuse | Open-source option |
| Custom logging | You'll regret it |

---

### 6. Secrets: Doppler or .env

**Rule**: Never hardcode API keys. Never commit `.env`.

**Options**:
| Approach | Best For |
|----------|----------|
| `.env` file | Solo/local dev |
| Doppler | Teams, multiple environments |
| AWS Secrets Manager | Enterprise/paranoid |

**Minimum viable**:
```bash
OPENAI_API_KEY=sk-...
SUPABASE_URL=https://...
SUPABASE_KEY=eyJ...
```

---

### 7. Email: SendGrid

**What it does**: Sends emails that actually arrive.

**Why SendGrid**:
- Deliverability
- Templates
- Analytics
- Free tier (100 emails/day)

**Why NOT Gmail API**:
- Rate limits (500/day)
- Deliverability issues
- OAuth complexity

Use Gmail for MVP testing, then switch.

---

### 8. Notifications: Slack

**What it does**: Tells you when things happen or break.

**Why Slack**:
- You're already there
- Webhooks are trivial
- Good mobile notifications

**What to notify**:
- New qualified lead
- Automation failure
- Token cost spike
- Daily summary

---

## What We Deliberately Avoided

| Trap | Why We Avoided It |
|------|-------------------|
| Custom models | Unnecessary complexity. Use APIs. |
| Kubernetes | Overkill for solo. Railway/Fly.io is fine. |
| Microservices | Monolith until proven otherwise. |
| NoSQL | Postgres handles everything. |
| Fancy frontends | Notion pages for client portals. |
| Blockchain/Web3 | No. |

---

## Future Upgrades (Not Now)

When you're past 10 clients:

1. **Vector search on historical data** — Use pgvector for "similar leads" analysis
2. **Multi-agent orchestration** — Graduate from single-agent to supervisor patterns
3. **Custom fine-tuned models** — Only if you have 10k+ examples
4. **White-label dashboard** — Replace Notion with real UI

But not now. Ship first.
