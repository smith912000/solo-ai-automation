-- =============================================================================
-- Lead Qualifier Automation - Supabase Schema
-- =============================================================================
-- Run this in your Supabase SQL Editor
-- =============================================================================

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- =============================================================================
-- LEADS TABLE
-- =============================================================================
-- Stores all leads with qualification data
-- Email is the unique identifier (deduplication key)

CREATE TABLE IF NOT EXISTS leads (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    client_id UUID NOT NULL,  -- For multi-tenant isolation
    
    -- Contact info
    email TEXT NOT NULL,
    name TEXT,
    company TEXT,
    website TEXT,
    phone TEXT,
    
    -- Source tracking
    source TEXT,  -- Where they came from (form, ad, referral)
    raw_form_data JSONB,  -- Original webhook payload
    
    -- Enrichment
    enrichment_json JSONB,  -- Industry, size, news, tech stack
    enriched_at TIMESTAMPTZ,
    
    -- Qualification
    qualification_score INTEGER,  -- 0-100
    qualification_label TEXT,  -- qualified, review, disqualified
    qualification_reason TEXT,
    personalization_points JSONB,  -- Array of strings
    
    -- Status
    status TEXT DEFAULT 'new',  -- new, qualified, contacted, converted, disqualified
    
    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    
    -- Constraints
    UNIQUE(client_id, email)
);

-- Index for fast lookups
CREATE INDEX IF NOT EXISTS idx_leads_client_email ON leads(client_id, email);
CREATE INDEX IF NOT EXISTS idx_leads_status ON leads(client_id, status);
CREATE INDEX IF NOT EXISTS idx_leads_score ON leads(client_id, qualification_score);

-- =============================================================================
-- RUNS TABLE
-- =============================================================================
-- Audit log for every automation execution
-- This is your observability + debugging backbone

CREATE TABLE IF NOT EXISTS runs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    client_id UUID NOT NULL,
    
    -- Idempotency
    idempotency_key TEXT UNIQUE NOT NULL,  -- hash(email + timestamp + source)
    
    -- Reference
    lead_id UUID REFERENCES leads(id),
    lead_email TEXT,
    automation_name TEXT DEFAULT 'lead-qualifier',
    
    -- Trigger info
    trigger_type TEXT DEFAULT 'webhook',  -- webhook, manual, scheduled
    trigger_payload JSONB,
    
    -- Execution trace
    steps_json JSONB,  -- Array of {step, status, duration_ms, output}
    decision_path TEXT,  -- Human-readable path taken
    
    -- Cost tracking
    llm_tokens_in INTEGER DEFAULT 0,
    llm_tokens_out INTEGER DEFAULT 0,
    llm_model TEXT,
    cost_estimate_usd NUMERIC(10, 4) DEFAULT 0,
    
    -- Result
    status TEXT DEFAULT 'pending',  -- pending, success, failed, killed
    error_message TEXT,
    error_stack TEXT,
    
    -- Timing
    started_at TIMESTAMPTZ DEFAULT NOW(),
    completed_at TIMESTAMPTZ,
    duration_ms INTEGER,
    
    -- Kill switch
    killed_by TEXT,  -- Which kill condition triggered
    killed_at TIMESTAMPTZ
);

-- Index for debugging
CREATE INDEX IF NOT EXISTS idx_runs_client ON runs(client_id);
CREATE INDEX IF NOT EXISTS idx_runs_lead ON runs(lead_id);
CREATE INDEX IF NOT EXISTS idx_runs_status ON runs(status);
CREATE INDEX IF NOT EXISTS idx_runs_created ON runs(started_at DESC);

-- =============================================================================
-- OUTBOX_EMAILS TABLE
-- =============================================================================
-- Approval queue for emails before sending
-- Essential for "approval mode" operation

CREATE TABLE IF NOT EXISTS outbox_emails (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    client_id UUID NOT NULL,
    
    -- References
    lead_id UUID REFERENCES leads(id),
    run_id UUID REFERENCES runs(id),
    
    -- Email content
    to_email TEXT NOT NULL,
    to_name TEXT,
    subject TEXT NOT NULL,
    body TEXT NOT NULL,
    
    -- Status
    status TEXT DEFAULT 'queued',  -- queued, approved, sent, rejected
    
    -- Approval
    approved_by TEXT,
    approved_at TIMESTAMPTZ,
    rejected_reason TEXT,
    
    -- Sending
    sent_at TIMESTAMPTZ,
    send_provider TEXT,  -- sendgrid, gmail
    send_response JSONB,
    
    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Index for queue processing
CREATE INDEX IF NOT EXISTS idx_outbox_client_status ON outbox_emails(client_id, status);
CREATE INDEX IF NOT EXISTS idx_outbox_lead ON outbox_emails(lead_id);

-- =============================================================================
-- EMAIL_HISTORY TABLE
-- =============================================================================
-- Track all sent emails to prevent spam
-- Used for "sent within X days" check

CREATE TABLE IF NOT EXISTS email_history (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    client_id UUID NOT NULL,
    
    lead_id UUID REFERENCES leads(id),
    lead_email TEXT NOT NULL,
    
    -- Email info
    subject TEXT,
    automation_name TEXT,
    
    -- Timestamps
    sent_at TIMESTAMPTZ DEFAULT NOW()
);

-- Index for spam prevention check
CREATE INDEX IF NOT EXISTS idx_email_history_lookup 
    ON email_history(client_id, lead_email, sent_at DESC);

-- =============================================================================
-- JOBS_QUEUE TABLE
-- =============================================================================
-- Intake enqueues jobs; worker claims via SKIP LOCKED + lease.

CREATE TABLE IF NOT EXISTS jobs_queue (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    client_id UUID NOT NULL,
    
    -- Job data
    lead_email TEXT NOT NULL,
    payload JSONB NOT NULL,
    job_type TEXT DEFAULT 'lead_qualify',
    priority INT DEFAULT 0,
    correlation_id TEXT,
    
    -- Status
    status TEXT DEFAULT 'queued',  -- queued, processing, done, failed, dead
    attempts INT DEFAULT 0,
    next_run_at TIMESTAMPTZ DEFAULT NOW(),
    error_message TEXT,
    
    -- Lease/locking
    locked_until TIMESTAMPTZ,
    locked_by TEXT,
    
    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_jobs_queue_status ON jobs_queue(status);
CREATE INDEX IF NOT EXISTS idx_jobs_queue_next_run ON jobs_queue(next_run_at);
CREATE INDEX IF NOT EXISTS idx_jobs_queue_locked_until ON jobs_queue(locked_until);
CREATE INDEX IF NOT EXISTS idx_jobs_queue_client_email ON jobs_queue(client_id, lead_email);
CREATE INDEX IF NOT EXISTS idx_jobs_queue_job_type ON jobs_queue(job_type);
CREATE INDEX IF NOT EXISTS idx_jobs_queue_priority ON jobs_queue(priority);

-- =============================================================================
-- JOBS_QUEUE CLAIM FUNCTION
-- =============================================================================
-- Claims the next available job using SKIP LOCKED and sets a lease.

CREATE OR REPLACE FUNCTION claim_next_job(worker_id TEXT, lease_seconds INT)
RETURNS SETOF jobs_queue AS $$
BEGIN
  RETURN QUERY
  WITH next_job AS (
    SELECT id
    FROM jobs_queue
    WHERE status = 'queued'
      AND next_run_at <= NOW()
      AND (locked_until IS NULL OR locked_until < NOW())
    ORDER BY created_at ASC
    FOR UPDATE SKIP LOCKED
    LIMIT 1
  )
  UPDATE jobs_queue
  SET status = 'processing',
      locked_until = NOW() + make_interval(secs => lease_seconds),
      locked_by = worker_id,
      attempts = attempts + 1,
      updated_at = NOW()
  WHERE id = (SELECT id FROM next_job)
  RETURNING *;
END;
$$ LANGUAGE plpgsql;

-- =============================================================================
-- SUPPRESSION_LIST TABLE
-- =============================================================================
-- Enforced in worker before send/queue.

CREATE TABLE IF NOT EXISTS suppression_list (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    client_id UUID NOT NULL,
    email TEXT NOT NULL,
    reason TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    
    UNIQUE(client_id, email)
);

CREATE INDEX IF NOT EXISTS idx_suppression_list_client_email ON suppression_list(client_id, email);

-- =============================================================================
-- AUTOMATION_STATUS TABLE
-- =============================================================================
-- Pause/resume control for each automation

CREATE TABLE IF NOT EXISTS automation_status (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    client_id UUID NOT NULL,
    automation_name TEXT NOT NULL,
    
    status TEXT DEFAULT 'active',  -- active, paused
    paused_at TIMESTAMPTZ,
    paused_by TEXT,
    pause_reason TEXT,
    
    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    
    UNIQUE(client_id, automation_name)
);

-- =============================================================================
-- HELPER FUNCTIONS
-- =============================================================================

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Apply to tables
DROP TRIGGER IF EXISTS update_leads_updated_at ON leads;
CREATE TRIGGER update_leads_updated_at
    BEFORE UPDATE ON leads
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_outbox_updated_at ON outbox_emails;
CREATE TRIGGER update_outbox_updated_at
    BEFORE UPDATE ON outbox_emails
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_automation_status_updated_at ON automation_status;
CREATE TRIGGER update_automation_status_updated_at
    BEFORE UPDATE ON automation_status
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_jobs_queue_updated_at ON jobs_queue;
CREATE TRIGGER update_jobs_queue_updated_at
    BEFORE UPDATE ON jobs_queue
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_crm_leads_updated_at ON crm_leads;
CREATE TRIGGER update_crm_leads_updated_at
    BEFORE UPDATE ON crm_leads
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_agent_tasks_updated_at ON agent_tasks;
CREATE TRIGGER update_agent_tasks_updated_at
    BEFORE UPDATE ON agent_tasks
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_voice_sessions_updated_at ON voice_sessions;
CREATE TRIGGER update_voice_sessions_updated_at
    BEFORE UPDATE ON voice_sessions
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- =============================================================================
-- CRM LEADS + STAGES (Agency Ops)
-- =============================================================================
-- Shared business pipeline tables for multi-agent orchestration.

CREATE TABLE IF NOT EXISTS crm_leads (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    client_id UUID NOT NULL,
    lead_id UUID REFERENCES leads(id),
    email TEXT NOT NULL,
    name TEXT,
    company TEXT,
    phone TEXT,
    source TEXT,
    stage TEXT DEFAULT 'prospect',  -- prospect, contacted, qualified, meeting, closed, lost
    score INTEGER,
    owner_agent TEXT,
    notes TEXT,
    metadata JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(client_id, email)
);

CREATE INDEX IF NOT EXISTS idx_crm_leads_client_stage ON crm_leads(client_id, stage);
CREATE INDEX IF NOT EXISTS idx_crm_leads_client_score ON crm_leads(client_id, score);

CREATE TABLE IF NOT EXISTS crm_stage_history (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    client_id UUID NOT NULL,
    crm_lead_id UUID REFERENCES crm_leads(id),
    from_stage TEXT,
    to_stage TEXT NOT NULL,
    changed_by TEXT,
    reason TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_crm_stage_history_lead ON crm_stage_history(crm_lead_id);

-- =============================================================================
-- AGENT TASKS + RUNS
-- =============================================================================

CREATE TABLE IF NOT EXISTS agent_tasks (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    client_id UUID NOT NULL,
    task_type TEXT NOT NULL,
    status TEXT DEFAULT 'queued',  -- queued, in_progress, done, failed, cancelled
    priority INT DEFAULT 0,
    payload JSONB,
    assigned_agent TEXT,
    correlation_id TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_agent_tasks_status ON agent_tasks(status);
CREATE INDEX IF NOT EXISTS idx_agent_tasks_client_type ON agent_tasks(client_id, task_type);

CREATE TABLE IF NOT EXISTS agent_runs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    client_id UUID NOT NULL,
    task_id UUID REFERENCES agent_tasks(id),
    agent_name TEXT NOT NULL,
    status TEXT DEFAULT 'started',  -- started, success, failed, skipped
    input_json JSONB,
    output_json JSONB,
    error_message TEXT,
    cost_estimate_usd NUMERIC(10, 4) DEFAULT 0,
    started_at TIMESTAMPTZ DEFAULT NOW(),
    completed_at TIMESTAMPTZ,
    duration_ms INTEGER
);

CREATE INDEX IF NOT EXISTS idx_agent_runs_task ON agent_runs(task_id);
CREATE INDEX IF NOT EXISTS idx_agent_runs_agent ON agent_runs(agent_name);

-- =============================================================================
-- VOICE SESSIONS + TURNS (Web Voice)
-- =============================================================================

CREATE TABLE IF NOT EXISTS voice_sessions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    client_id UUID NOT NULL,
    crm_lead_id UUID REFERENCES crm_leads(id),
    status TEXT DEFAULT 'active',  -- active, completed, failed
    channel TEXT DEFAULT 'web',
    metadata JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_voice_sessions_client ON voice_sessions(client_id);

CREATE TABLE IF NOT EXISTS voice_turns (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id UUID REFERENCES voice_sessions(id),
    role TEXT NOT NULL,  -- user, assistant, system
    content TEXT NOT NULL,
    action TEXT,
    confidence NUMERIC(5, 2),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_voice_turns_session ON voice_turns(session_id);

-- =============================================================================
-- KPI SNAPSHOTS + EXPERIMENTS
-- =============================================================================

CREATE TABLE IF NOT EXISTS kpi_snapshots (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    client_id UUID NOT NULL,
    period_start TIMESTAMPTZ NOT NULL,
    period_end TIMESTAMPTZ NOT NULL,
    metrics JSONB NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_kpi_snapshots_client ON kpi_snapshots(client_id, period_start DESC);

CREATE TABLE IF NOT EXISTS experiments (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    client_id UUID NOT NULL,
    name TEXT NOT NULL,
    hypothesis TEXT,
    status TEXT DEFAULT 'active',  -- active, paused, completed, cancelled
    config JSONB,
    results JSONB,
    started_at TIMESTAMPTZ DEFAULT NOW(),
    completed_at TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS idx_experiments_client ON experiments(client_id, status);

-- =============================================================================
-- COST EVENTS (All-in tracking)
-- =============================================================================

CREATE TABLE IF NOT EXISTS cost_events (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    client_id UUID NOT NULL,
    category TEXT NOT NULL,  -- llm, email, voice, infra, human_time
    provider TEXT,
    automation_name TEXT,
    run_id UUID,
    task_id UUID,
    quantity NUMERIC(12, 4) DEFAULT 0,
    unit_cost_usd NUMERIC(12, 6) DEFAULT 0,
    cost_usd NUMERIC(12, 6) DEFAULT 0,
    metadata JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_cost_events_client ON cost_events(client_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_cost_events_category ON cost_events(category);
CREATE INDEX IF NOT EXISTS idx_cost_events_automation ON cost_events(automation_name);

-- =============================================================================
-- ROW LEVEL SECURITY (Optional but recommended)
-- =============================================================================
-- Uncomment these if you're using Supabase Auth for client access

-- ALTER TABLE leads ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE runs ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE outbox_emails ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE email_history ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE automation_status ENABLE ROW LEVEL SECURITY;

-- Example RLS policy (adjust auth.uid() mapping as needed):
-- CREATE POLICY "Users can only see their own leads"
--     ON leads FOR ALL
--     USING (client_id = auth.uid());

-- =============================================================================
-- SAMPLE DATA (for testing)
-- =============================================================================
-- Uncomment to insert test data

-- INSERT INTO leads (client_id, email, name, company, status)
-- VALUES 
--     ('00000000-0000-0000-0000-000000000001', 'test@example.com', 'Test User', 'Acme Corp', 'new');
