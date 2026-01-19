# Vapi Dashboard Setup Plan

> **Goal**: Configure Vapi.ai dashboard to enable AI voice calling for Solo AI Automation

---

## Prerequisites
- [x] Vapi account created
- [x] API keys obtained (Private + Public)
- [x] Keys added to `.env`

---

## Setup Checklist

### 1. Phone Number (Required for Outbound)
- [ ] Go to **Phone Numbers** → **Buy Number**
- [ ] Choose a US number (+1) for business calls
- [ ] Cost: ~$2/month per number
- [ ] Note the **Phone Number ID** for API calls

### 2. Create Assistant
- [ ] Go to **Assistants** → **Create Assistant**
- [ ] Name: `Solo AI Sales Agent`
- [ ] Configure:

| Setting | Value |
|---------|-------|
| **First Message** | "Hi, this is Alex from Solo AI Automation. Is now a good time for a quick 30-second overview?" |
| **Model** | GPT-4o-mini (cost-effective) |
| **Voice** | 11Labs → Rachel (professional female) or Adam (professional male) |
| **Max Duration** | 5 minutes |
| **End Call Phrases** | "goodbye", "not interested", "remove me" |

### 3. System Prompt Template
```
You are Alex, a friendly AI sales representative for Solo AI Automation.

GOAL: Qualify leads and book discovery calls.

STYLE:
- Warm, professional, concise
- Never pushy or aggressive
- Respect "no" immediately

SCRIPT FLOW:
1. Introduce yourself (10 sec)
2. Ask if they have 30 seconds
3. If yes: Give 1-sentence value prop
4. Ask: "Would a quick 15-min call with our team be helpful?"
5. If yes: "Great, I'll have someone reach out. Best email?"
6. Thank and end

OBJECTION HANDLING:
- "Not interested" → "No problem at all. Thanks for your time!"
- "How did you get my number?" → "We found you through [source]. I can remove you from our list."
- "Send me an email" → "Absolutely. What's the best email?"

NEVER:
- Argue or push back
- Make false claims
- Continue after "no"
```

### 4. Configure Voice Settings
| Setting | Recommended |
|---------|-------------|
| **Provider** | ElevenLabs |
| **Voice ID** | `21m00Tcm4TlvDq8ikWAM` (Rachel) |
| **Stability** | 0.5 |
| **Similarity** | 0.75 |
| **Speaking Rate** | 1.0 |

### 5. Webhook Configuration
- [ ] Go to **Settings** → **Webhooks**
- [ ] Set **Server URL**: `https://web-production-9f9f0.up.railway.app/voice/webhook`
- [ ] Enable events:
  - `call.started`
  - `call.ended`
  - `transcript.update`
  - `function.call`

### 6. Test Call
- [ ] Use Vapi's **Test Call** feature
- [ ] Call your own phone to verify:
  - Voice clarity
  - Response timing
  - Script flow
  - End call triggers

---

## Cost Estimate

| Component | Cost |
|-----------|------|
| Phone Number | $2/month |
| Vapi Usage | ~$0.05/min |
| ElevenLabs Voice | Included |
| OpenAI (GPT-4o-mini) | ~$0.01/min |

**Example**: 100 calls × 3 min avg = $18/month

---

## Integration with Solo AI

### Current Code Flow:
```
1. Worker picks up "voice_call" job
2. place_call() sends request to Vapi
3. Vapi initiates call with assistant config
4. Call events posted to /voice/webhook
5. Transcripts stored in voice_turns table
```

### To Complete:
- [ ] Add `/voice/webhook` endpoint for Vapi callbacks
- [ ] Store transcripts and outcomes
- [ ] Update CRM with call results

---

## Files to Update

| File | Change |
|------|--------|
| `.env` | Add `VAPI_PHONE_NUMBER_ID` after buying number |
| `api/routes/voice.py` | Add webhook endpoint |
| `worker/main.py` | Add `voice_call` job handler |

---

## Quick Reference

| Item | Value |
|------|-------|
| Dashboard | https://dashboard.vapi.ai |
| API Docs | https://docs.vapi.ai |
| Your Private Key | `a4f981ea-...` (in .env) |
| API Endpoint | `https://api.vapi.ai/call/phone` |
