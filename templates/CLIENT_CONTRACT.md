# Client Contract Template

> **Note:** This is a template. Consult a lawyer before using.

---

## Automation Services Agreement

**Between:**

**Provider:** [Your Company Name]  
**Client:** [Client Company Name]  
**Effective Date:** [DATE]

---

## 1. Scope of Services

### 1.1 Automation(s) Included

| Automation | Description |
|------------|-------------|
| Lead Qualifier | Qualify website leads and draft personalized emails |

### 1.2 What Is Automated

- ✅ Receiving webhooks from website forms
- ✅ Qualifying leads based on defined criteria
- ✅ Enriching leads with company data
- ✅ Drafting personalized email responses
- ✅ Logging all activity
- ✅ Sending notifications via Slack

### 1.3 What Requires Human Review

- ⚠️ Approving emails before sending (if approval mode enabled)
- ⚠️ Updating qualification rubric
- ⚠️ Handling edge cases flagged for review

### 1.4 What Is NOT Included

- ❌ Responding to customer replies
- ❌ Managing email threads
- ❌ Building custom integrations beyond scope
- ❌ 24/7 on-call support

---

## 2. Service Level Agreement (SLA)

| Metric | Target | Measurement |
|--------|--------|-------------|
| Processing time | < 2 minutes | Time from webhook to email queue |
| Uptime | 99% monthly | Excluding scheduled maintenance |
| Error rate | < 5% | Runs failed / total runs |
| Support response | < 24 hours | Business days only |

### SLA Credits

| Performance | Credit |
|-------------|--------|
| 95-99% uptime | 10% of monthly fee |
| 90-95% uptime | 25% of monthly fee |
| < 90% uptime | 50% of monthly fee |

---

## 3. Pricing

### 3.1 Monthly Fee

| Component | Amount |
|-----------|--------|
| Base fee | $______/month |
| Included leads | ______ leads/month |
| Overage rate | $____ per additional lead |

### 3.2 One-Time Setup

| Component | Amount |
|-----------|--------|
| Initial configuration | $______ |
| Custom rubric development | $______ (if applicable) |
| CRM integration | $______ (if applicable) |

### 3.3 Payment Terms

- Net 15 from invoice date
- Late payments accrue 1.5% monthly interest
- Service may be paused for payments > 30 days overdue

---

## 4. Data Handling

### 4.1 Data Processed

| Data Type | Purpose | Retention |
|-----------|---------|-----------|
| Lead contact info | Qualification + emailing | While service active |
| Company data | Enrichment | While service active |
| Run logs | Debugging + audit | 90 days |
| Email content | Sending + audit | 90 days |

### 4.2 Data Security

- All data encrypted in transit (TLS 1.3)
- Database encryption at rest
- Access limited to necessary personnel
- No data used for model training

### 4.3 Client Data Separation

Client data is isolated at the database level. No access to other clients' data.

### 4.4 Data Deletion

Upon termination, data deleted within 30 days of written request.

---

## 5. Responsibilities

### 5.1 Provider Responsibilities

- [ ] Configure and deploy automation
- [ ] Monitor for errors and alerts
- [ ] Maintain 99% uptime
- [ ] Respond to support requests within SLA
- [ ] Provide monthly usage reports

### 5.2 Client Responsibilities

- [ ] Provide webhook endpoint details
- [ ] Define qualification criteria/rubric
- [ ] Review and approve emails (if approval mode)
- [ ] Provide CRM credentials (if integration needed)
- [ ] Notify of any issues promptly
- [ ] Pay invoices per terms

---

## 6. Failure Handling

### 6.1 Automatic Safeguards

| Situation | Automatic Response |
|-----------|-------------------|
| Duplicate webhook | Skip processing |
| Same lead emailed recently | Skip email, log |
| Token cost spike | Halt, alert |
| API failures | Retry 2x, then halt |
| Invalid output | Route to review queue |

### 6.2 Incident Response

1. Automation paused automatically
2. Provider alerted via monitoring
3. Client notified within 4 hours
4. Root cause analysis within 24 hours
5. Prevention measures implemented

---

## 7. Liability

### 7.1 Limitation

Provider's total liability capped at 12 months of fees paid.

### 7.2 Exclusions

Provider not liable for:
- Consequential, indirect, or punitive damages
- Lost revenue or opportunities
- Client's use of AI-generated content
- Third-party service outages

### 7.3 AI Disclaimer

Client acknowledges that AI outputs may contain errors or produce unexpected results. Human review is recommended before acting on AI outputs.

---

## 8. Term & Termination

### 8.1 Initial Term

_______ months from Effective Date.

### 8.2 Renewal

Auto-renews monthly unless cancelled with 30 days notice.

### 8.3 Termination for Cause

Either party may terminate immediately for material breach (15-day cure period for correctable breaches).

### 8.4 Effect of Termination

- Outstanding fees become due immediately
- Client access revoked
- Provider retains logs per retention policy
- Client data deleted per Section 4.4

---

## 9. Signatures

**Provider:**

Name: _________________________  
Title: _________________________  
Date: _________________________  
Signature: _________________________

**Client:**

Name: _________________________  
Title: _________________________  
Date: _________________________  
Signature: _________________________

---

## Exhibit A: Qualification Rubric

*[Attach customized rubric from config.py]*

## Exhibit B: Integration Details

| System | Details |
|--------|---------|
| Webhook URL | |
| CRM | |
| Email provider | |
| Notification channel | |
