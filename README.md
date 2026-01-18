# Solo AI Automation Business

> **Mission**: Build deterministic business processes with probabilistic reasoning inserted only where judgment is required.

You are not a developer. You are a **System Architect & Agent Supervisor**.

---

## Quick Start

1. **Set up external services**:
   - Create a [Supabase](https://supabase.com) project
   - Deploy [n8n](https://n8n.io) (self-hosted or cloud)
   - Set up [LangSmith](https://smith.langchain.com) for observability

2. **Configure secrets**:
   - Create a `.env` file in the project root
   - See [docs/ENVIRONMENT.md](docs/ENVIRONMENT.md) for required values

3. **Run the database schema**:
   ```sql
   -- In Supabase SQL editor, run:
   -- automations/lead-qualifier/schema.sql
   ```

4. **Run the API intake endpoint**:
   - Start the API server and expose `POST /webhook/lead`

5. **(Optional) Import the n8n workflow**:
   - Use n8n only for downstream connector actions
   - Import `automations/lead-qualifier/n8n-workflow.json` if needed

6. **Test with a sample webhook**:
   ```bash
   curl -X POST https://your-api-host.com/webhook/lead \
     -H "X-API-Key: your_api_key" \
     -H "Content-Type: application/json" \
     -d '{"name":"Test","email":"test@example.com","company":"Acme","message":"Hello"}'
   ```

---

## Deployment (Railway)

1. **Create the API service**:
   - Connect the repo in Railway
   - Build uses `Dockerfile`
   - Start command (already in `railway.json`):  
     `uvicorn api.main:app --host 0.0.0.0 --port $PORT`

2. **Create a worker service** (separate Railway service):
   - Use the same repo and environment variables
   - Start command: `python -m worker.main`
   - Set `OUTBOX_SEND_ENABLED=true` if you want approved emails sent
   - Optional: run a dedicated outbox sender with `python -m worker.outbox_sender`

3. **Verify**:
   - API returns `{"status": "ok"}` at `/`
   - Worker logs show job polling

---

## Local Docker

```bash
docker build -t solo-ai-automation .
docker run --rm -p 8000:8000 --env-file .env solo-ai-automation
```

Run the worker locally (outside Docker) or as a second container:

```bash
python -m worker.main
```

## Project Structure

```
├── docs/                  # Core business documentation
├── automations/           # Production automations
│   └── lead-qualifier/    # First automation: Lead → Qualify → Email
├── lib/                   # Reusable Python utilities
├── assets/                # Client-facing materials
├── templates/             # Contract & onboarding templates
└── ops/                   # Solo operator playbooks
```

---

## Documentation

| Document | Purpose |
|----------|---------|
| [Business Model](docs/BUSINESS_MODEL.md) | 3 viable solo models + pricing |
| [Tech Stack](docs/TECH_STACK.md) | Stack decisions + rationale |
| [Ceiling Limits](docs/CEILING_LIMITS.md) | Hard constraints to prevent collapse |
| [Safety Protocols](docs/SAFETY_PROTOCOLS.md) | Kill switches + safeguards |
| [Failure Catalog](docs/FAILURE_CATALOG.md) | Failures as assets |
| [Command Center](docs/COMMAND_CENTER.md) | Dashboard overview |
| [Production Monitoring](ops/PRODUCTION_MONITORING.md) | Ops checklist |

---

## First Automation: Lead Qualifier

**Trigger**: Website form submit (webhook)  
**Flow**: Form → Dedupe → Enrich → Qualify → Draft Email → Send/Queue → Log  
**SLA**: 99% of leads processed within 2 minutes

See [automations/lead-qualifier/README.md](automations/lead-qualifier/README.md) for full spec.

## Stub Automations (Optional)

- Outreach Agent (cold email): `POST /outreach/draft`
- Voice AI (calls): `POST /voice/call`
- Client Onboarder: `POST /onboarder/checklist`

---

## Core Philosophy

1. **If you can't explain it in 5 minutes on a whiteboard, it's too complex**
2. **Treat failures as assets, not bugs**
3. **Every automation needs a kill switch**
4. **Reliability is a feature**

---

## License

Proprietary. All rights reserved.
