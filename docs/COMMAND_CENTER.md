# Command Center Dashboard

The command center is a lightweight operational dashboard served at `/dashboard`.

## What It Shows

- Queue counts (jobs)
- Outbox counts (queued/approved/sent/rejected)
- Run counts (success/failed/killed/skipped)
- Recent runs with status and cost

## How It Works

- The page calls `GET /admin/metrics`
- You must provide `X-API-Key` (and optional `X-Client-Id`)

## Next.js Command Center UI

The full Command Center UI lives in `command-center/` (Next.js).

Run it locally:
```
cd command-center
npm install
npm run dev
```

Configuration:
- `X-API-Key` and optional `X-Client-Id` are entered in the UI
- Set `NEXT_PUBLIC_API_BASE` if the API is hosted elsewhere

## Security

Keep the dashboard behind your admin API key. Do not expose it publicly without auth.
# Command Center — Architecture

> The brain of the operation. One screen to rule them all.

---

## Overview

The Command Center is a **real-time web dashboard** that provides:
- Complete visibility into all business operations
- Control over every AI agent
- Human-in-the-loop approval workflows
- Analytics and optimization insights

---

## Progress Tracker

Use this section as the single source of truth. Each update should include:
- Status change (⬜ Not started / 🟡 In progress / ✅ Complete / 🔴 Blocked)
- Last check date
- Next action required
- Owner (agent/role)

| Area | Status | Last Check | Owner | Next Action | Notes |
|------|--------|-----------|-------|-------------|-------|
| Intake API (`/webhook/lead`) | ✅ Complete | 2026-01-18 | Core | None | Live in FastAPI |
| Worker (jobs_queue) | ✅ Complete | 2026-01-18 | Core | None | Claim + process loop |
| Suppression list | ✅ Complete | 2026-01-18 | Core | None | Admin endpoints + enforcement |
| Slack notifications | 🟡 In progress | 2026-01-18 | SlackAgent | Verify delivery + wire failures/alerts | `lib/slack.py` wired; delivery unverified |
| Command Center UI | 🟡 Basic | 2026-01-18 | UIAgent | Wire to API endpoints | Next.js scaffold exists; `/dashboard` is placeholder |
| Approvals UI | ⬜ Not started | 2026-01-18 | UIAgent | Build outbox queue viewer + approve/reject | Depends on outbox queue |
| Analytics UI | ⬜ Not started | 2026-01-18 | UIAgent | Add metrics endpoints + charts | Depends on API metrics |

### Stubbed vs Live

| Component | Status | Notes |
|-----------|--------|-------|
| `/api/analytics/revenue` | Stubbed | Returns static 0.0 |
| Role handlers (agency-ops) | Stubbed | Return static payloads |
| KPI/optimization jobs | Partial | Logic exists, no scheduler wired |

---

## Technology Stack

| Layer | Technology | Why |
|-------|------------|-----|
| **Frontend** | Next.js + React | Fast, SSR, great DX |
| **Styling** | Tailwind CSS | Rapid iteration |
| **Real-time** | WebSockets / Supabase Realtime | Live updates |
| **Charts** | Recharts or Tremor | Clean analytics |
| **Auth** | Supabase Auth | Already integrated |
| **Backend** | Existing FastAPI | Reuse API |
| **Database** | Supabase (Postgres) | Already in place |

---

## Core Modules

### 1. Dashboard (Home)

**Purpose**: At-a-glance health of the entire business.

```
┌──────────────────────────────────────────────────────────────┐
│  🟢 All Systems Operational              Last update: 2s ago │
├──────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐           │
│  │   $45,200   │  │     127     │  │    94.2%    │           │
│  │     MRR     │  │   Clients   │  │   Uptime    │           │
│  └─────────────┘  └─────────────┘  └─────────────┘           │
│                                                               │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐           │
│  │     $892    │  │     23      │  │      4      │           │
│  │ Today Spend │  │ Leads Today │  │ Deals Close │           │
│  └─────────────┘  └─────────────┘  └─────────────┘           │
│                                                               │
│  [Pipeline Chart]  [Revenue Chart]  [Agent Activity]         │
│                                                               │
└──────────────────────────────────────────────────────────────┘
```

**Data Sources**:
- `runs` table → activity
- `leads` table → pipeline
- `jobs_queue` table → backlog and processing health
- Stripe/payment system → revenue
- Cost tracker → spend

---

### 2. Pipeline

**Purpose**: Visualize and control the entire sales funnel.

```
┌─────────────────────────────────────────────────────────────┐
│  PIPELINE                                    [+ Add Lead]    │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  Prospects    Contacted    Qualified    Meeting    Closed    │
│  ┌────────┐   ┌────────┐   ┌────────┐   ┌──────┐  ┌──────┐  │
│  │  342   │→  │  128   │→  │   47   │→  │  12  │→ │   4  │  │
│  │ leads  │   │ leads  │   │ leads  │   │ calls│  │deals │  │
│  └────────┘   └────────┘   └────────┘   └──────┘  └──────┘  │
│                                                              │
│  ┌────────────────────────────────────────────────────────┐ │
│  │ Lead                   Score    Status      Actions    │ │
│  ├────────────────────────────────────────────────────────┤ │
│  │ john@acme.com           78     Qualified   [View][Call]│ │
│  │ sarah@bigco.com         92     Meeting     [View][Prep]│ │
│  │ mike@startup.io         45     Review      [View][Skip]│ │
│  └────────────────────────────────────────────────────────┘ │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

**Actions Available**:
- Approve/reject leads
- Trigger outreach
- Schedule calls
- Move between stages
- Add notes

---

### 3. Agents

**Purpose**: Monitor and control all AI agents.

```
┌─────────────────────────────────────────────────────────────┐
│  AGENTS                              [+ Deploy New Agent]    │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌─────────────────────────────────────────────────────────┐│
│  │ Agent          Status    Success   Cost/24h   Actions   ││
│  ├─────────────────────────────────────────────────────────┤│
│  │ 🟢 Qualifier   Active     94.2%    $12.40    [Pause]    ││
│  │ 🟢 Email Draft Active     98.1%    $8.20     [Pause]    ││
│  │ 🟡 Outreach    Paused     87.3%    $0.00     [Resume]   ││
│  │ 🔴 Caller      Error      --       --        [Logs]     ││
│  │ ⚪ Onboarder   Planned    --       --        [Deploy]   ││
│  └─────────────────────────────────────────────────────────┘│
│                                                              │
│  [Agent Performance Chart]  [Cost Breakdown]                 │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

**Agent Detail View**:
- Configuration
- Recent runs (with logs)
- Performance metrics
- Cost history
- Pause/resume/restart controls

---

### 4. Clients

**Purpose**: Manage all client relationships.

```
┌─────────────────────────────────────────────────────────────┐
│  CLIENTS                              [+ New Client]         │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌─────────────────────────────────────────────────────────┐│
│  │ Client         MRR     Health   Automations   Actions   ││
│  ├─────────────────────────────────────────────────────────┤│
│  │ Acme Corp    $2,000    🟢 Good      3        [Manage]   ││
│  │ BigCo Inc    $1,500    🟡 Warning   2        [Manage]   ││
│  │ Startup.io   $500      🟢 Good      1        [Manage]   ││
│  └─────────────────────────────────────────────────────────┘│
│                                                              │
│  [Revenue by Client]  [Churn Risk]  [Upsell Opportunities]   │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

**Client Detail View**:
- Contract details
- Active automations
- Usage metrics
- Communication history
- Billing status

---

### 5. Approvals

**Purpose**: Human-in-the-loop for high-stakes actions.

```
┌─────────────────────────────────────────────────────────────┐
│  APPROVALS                               12 pending          │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌─────────────────────────────────────────────────────────┐│
│  │ Type       To               Preview            Actions  ││
│  ├─────────────────────────────────────────────────────────┤│
│  │ Email     john@acme.com    "Hi John, I noticed..." [✓][✗]││
│  │ Email     sarah@big.com    "Following up on..."   [✓][✗]││
│  │ Call      mike@startup.io  Script preview...      [✓][✗]││
│  │ Proposal  tech@corp.com    $3,500/mo package      [✓][✗]││
│  └─────────────────────────────────────────────────────────┘│
│                                                              │
│  [Approve All Safe]  [Reject Selected]  [Edit Before Send]   │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

**Approval Types**:
- Outreach emails
- Follow-up messages
- Call scripts
- Proposals/quotes
- Contract changes

---

### 6. Analytics

**Purpose**: Deep insights into business performance.

```
┌─────────────────────────────────────────────────────────────┐
│  ANALYTICS                        [Export] [Date Range ▼]   │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  Revenue          Costs           Margin         Growth      │
│  ┌──────────┐    ┌──────────┐    ┌──────────┐  ┌──────────┐ │
│  │ $45,200  │    │  $4,890  │    │   89.2%  │  │  +12.3%  │ │
│  │   MRR    │    │ Monthly  │    │  Margin  │  │  MoM     │ │
│  └──────────┘    └──────────┘    └──────────┘  └──────────┘ │
│                                                              │
│  [Revenue Over Time]                                         │
│  ▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓░░░░░░░░░░░░░░░░░░░░░░░             │
│                                                              │
│  [Agent ROI]  [CAC/LTV]  [Churn Analysis]  [Cost Attribution]│
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

**Key Metrics**:
- Revenue (MRR, ARR, growth)
- Costs (LLM, infra, human time)
- Agent performance (success rate, cost per action)
- Sales metrics (CAC, LTV, conversion rates)
- Operational metrics (response time, resolution time)

---

### 7. Settings

**Purpose**: Configure system-wide settings.

- Kill switch controls
- Budget limits
- Notification preferences
- API keys management
- Team access (future)
- Billing settings

---

## Real-Time Features

| Feature | Implementation |
|---------|----------------|
| Live lead updates | Supabase Realtime subscription |
| Agent status | WebSocket from worker |
| Approval notifications | Push + sound alert |
| Cost alerts | Threshold trigger |
| System health | Heartbeat checks |

---

## API Endpoints Needed

```
POST /webhook/lead             → Intake (primary trigger)
GET  /status                   → Queue/worker health
GET  /admin/suppression         → List suppression entries
POST /admin/suppression         → Add suppression entry
DELETE /admin/suppression/{id}  → Remove suppression entry

GET  /api/dashboard/stats      → Dashboard metrics
GET  /api/pipeline             → All leads by stage
GET  /api/agents               → Agent list + status
GET  /api/agents/{id}/runs     → Agent run history
POST /api/agents/{id}/pause    → Pause agent
POST /api/agents/{id}/resume   → Resume agent
GET  /api/clients              → Client list
GET  /api/clients/{id}         → Client detail
GET  /api/approvals            → Pending approvals
POST /api/approvals/{id}/approve → Approve action
POST /api/approvals/{id}/reject  → Reject action
GET  /api/analytics/revenue    → Revenue data
GET  /api/analytics/costs      → Cost breakdown
```

---

## Development Phases

### v0.1 — Basic Dashboard (Week 1)
- [ ] Dashboard with key metrics
- [ ] Pipeline view (read-only)
- [ ] Approval queue (functional)
- [ ] Basic auth

### v0.2 — Agent Control (Week 2)
- [ ] Agent list and status
- [ ] Pause/resume controls
- [ ] Run history viewer
- [ ] Cost tracking display

### v0.3 — Full Operations (Week 3)
- [ ] Client management
- [ ] Analytics charts
- [ ] Real-time updates
- [ ] Settings panel

### v0.4 — Advanced (Week 4+)
- [ ] AI agent deployment from UI
- [ ] A/B testing controls
- [ ] Custom report builder
- [ ] Mobile responsive

---

## File Structure

```
command-center/
├── app/                    # Next.js app directory
│   ├── page.tsx            # Dashboard
│   ├── pipeline/
│   ├── agents/
│   ├── clients/
│   ├── approvals/
│   ├── analytics/
│   └── settings/
├── components/
│   ├── ui/                 # Shadcn/ui components
│   ├── charts/
│   ├── tables/
│   └── layouts/
├── lib/
│   ├── supabase.ts
│   ├── api.ts
│   └── utils.ts
└── public/
```

---

## Next Step

When ready to build:

1. Initialize Next.js project
2. Connect to existing Supabase
3. Build dashboard with mock data
4. Wire up real API endpoints
5. Add real-time subscriptions
