# Client Onboarding Checklist

> Complete this checklist for each new client.

---

## Client Info

| Field | Value |
|-------|-------|
| Client Name | |
| Contact Name | |
| Contact Email | |
| Contract Signed | ☐ Yes |
| Start Date | |
| Package | ☐ Starter / ☐ Growth / ☐ Pro |

---

## Phase 1: Discovery (Day 1)

### Gather Requirements

- [ ] Current lead volume (leads/month)
- [ ] Lead sources (website forms, ads, etc.)
- [ ] Existing CRM system
- [ ] Email provider (Gmail, Outlook, other)
- [ ] Desired response time
- [ ] Industry/vertical
- [ ] Ideal customer profile

### Define Qualification Criteria

- [ ] What makes a "qualified" lead?
- [ ] What industries to prioritize?
- [ ] Company size preferences?
- [ ] Budget signals to look for?
- [ ] Deal-breakers (auto-disqualify)?

### Technical Details

- [ ] Website form solution (Typeform, HubSpot, custom?)
- [ ] Can they add webhook to form?
- [ ] CRM API access available?
- [ ] Email sending domain (for SPF/DKIM)

---

## Phase 2: Configuration (Days 2-3)

### Database Setup

- [ ] Create client_id in system
- [ ] Test database connection
- [ ] Verify table isolation

### Webhook Configuration

- [ ] Get webhook endpoint details
- [ ] Test webhook receives data
- [ ] Validate field mapping:
  - [ ] name → name
  - [ ] email → email
  - [ ] company → company
  - [ ] website → website
  - [ ] message → message

### Qualification Setup

- [ ] Customize rubric in config
- [ ] Update offer description
- [ ] Set scoring thresholds
- [ ] Test with sample leads

### Email Setup

- [ ] Configure sender domain
- [ ] Verify SPF/DKIM
- [ ] Set reply-to address
- [ ] Create email signature
- [ ] Test email deliverability

### Integration

- [ ] CRM connection (if applicable)
- [ ] Slack channel for notifications
- [ ] Set up client-specific alerts

---

## Phase 3: Testing (Days 4-5)

### Approval Mode Enabled

- [ ] Send 5 test leads
- [ ] Review qualification scores
- [ ] Review email drafts
- [ ] Client approves messaging tone
- [ ] Adjust rubric if needed

### Validation

| Test | Result |
|------|--------|
| Form → Webhook working | ☐ Pass |
| Lead created in DB | ☐ Pass |
| Qualification runs | ☐ Pass |
| Email drafted correctly | ☐ Pass |
| Email lands in inbox (not spam) | ☐ Pass |
| Slack notification received | ☐ Pass |
| Run log complete | ☐ Pass |

### Edge Cases

- [ ] Test with minimal data (name + email only)
- [ ] Test with very long message
- [ ] Test duplicate submission
- [ ] Test invalid email format

---

## Phase 4: Training (Day 5)

### Client Training Call

- [ ] Explain approval queue workflow
- [ ] Show how to approve/reject emails
- [ ] Show Slack notifications
- [ ] Explain scoring system
- [ ] Share runbook for emergencies
- [ ] Answer questions

### Documentation Provided

- [ ] One-pager for reference
- [ ] Terms of Service signed
- [ ] Emergency contact info
- [ ] Escalation process

---

## Phase 5: Launch (Week 2)

### Soft Launch (Days 1-3)

- [ ] Enable on 20% of traffic
- [ ] Monitor error rates
- [ ] Check email open rates
- [ ] Gather initial feedback

### Adjust

- [ ] Tune qualification thresholds
- [ ] Refine email templates
- [ ] Fix any integration issues

### Full Launch (Days 4+)

- [ ] Enable on 100% traffic
- [ ] Disable approval mode (if client ready)
- [ ] Set up weekly summary report
- [ ] Schedule 30-day review call

---

## Phase 6: Ongoing

### Weekly

- [ ] Send usage summary to client
- [ ] Review any failed runs
- [ ] Check token costs vs budget

### Monthly

- [ ] Review qualification accuracy
- [ ] Gather client feedback
- [ ] Adjust rubric if conversion data available
- [ ] Invoice sent

### Quarterly

- [ ] Business review call
- [ ] Discuss expansion opportunities
- [ ] Rotate API keys

---

## Troubleshooting Contacts

| Issue | Contact |
|-------|---------|
| Technical emergency | [Your phone] |
| Billing questions | [Billing email] |
| Feature requests | [Support email] |

---

## Sign-Off

| Milestone | Client Sign-Off | Date |
|-----------|-----------------|------|
| Configuration complete | | |
| Testing passed | | |
| Training complete | | |
| Soft launch approved | | |
| Full launch approved | | |
