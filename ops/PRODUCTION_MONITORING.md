# Production Monitoring

## Core Checks

- Queue depth is stable and not growing
- Recent runs show mostly `success` / `skipped`
- Outbox queue is drained regularly
- Cost per run stays under `MAX_COST_PER_RUN_USD`

## API Endpoints

- `GET /health` basic liveness check
- `GET /status` queue counts
- `GET /admin/metrics` full operational metrics

## Suggested Routine

- Daily: check outbox, run failures, and cost spikes
- Weekly: review qualification accuracy + email outcomes
- Monthly: review spend vs margin and rotate keys

## Background Workers

- `worker/main.py` processes jobs_queue
- `worker/outbox_sender.py` sends approved emails
