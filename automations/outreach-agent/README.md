# Outreach Agent (Cold Email)

> **Purpose**: Generate personalized cold outreach emails for prospects.

## Trigger

- Manual run or batch job from a prospect list
- Inputs: name, company, role, pain points, and website

## Output

- Email subject
- Email body (under 150 words)
- Suggested follow-up action

## Files

| File | Purpose |
|------|---------|
| `agent/config.py` | Model + prompt config |
| `agent/cold_emailer.py` | Drafting logic |
| `agent/main.py` | CLI entry point |

## Notes

- This module is standalone and not wired into the intake flow yet.
- Add sequencing and CRM sync when deploying to production.
