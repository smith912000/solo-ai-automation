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
