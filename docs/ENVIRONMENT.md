# Environment Variables

Create a `.env` file in the project root with the following values.

## Required

- `SUPABASE_URL`
- `SUPABASE_KEY`
- `DEFAULT_CLIENT_ID`
- `API_KEY`
- `PASSWORD` (optional password-based access)
- `OPENAI_API_KEY`
- `SENDGRID_API_KEY`
- `SENDGRID_FROM_EMAIL`

## Optional (recommended)

- `ADMIN_API_KEY` (defaults to `API_KEY` if unset)
- `ADMIN_PASSWORD` (optional password for admin routes)
- `SENDGRID_FROM_NAME`
- `REASONING_MODEL` (default: `gpt-4o`)
- `DRAFTING_MODEL` (default: `gpt-4o-mini`)
- `APPROVAL_MODE` (default: `true`)
- `EMAIL_COOLDOWN_DAYS` (default: `7`)
- `MAX_TOKENS_PER_RUN` (default: `5000`)
- `MAX_COST_PER_RUN_USD` (default: `0.50`)
- `MAX_RETRIES_PER_STEP` (default: `2`)
- `MAX_EXECUTION_TIME_SECONDS` (default: `300`)
- `WORKER_ID` (default: `worker-1`)
- `QUEUE_LEASE_SECONDS` (default: `120`)
- `QUEUE_MAX_ATTEMPTS` (default: `5`)
- `WORKER_POLL_SECONDS` (default: `2`)
- `OUTBOX_POLL_SECONDS` (default: `10`)
- `OUTBOX_BATCH_SIZE` (default: `10`)
- `PREFILTER_BLOCKED_DOMAINS` (comma-separated list)
