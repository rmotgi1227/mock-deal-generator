# Mock Deal Generator

Generates realistic synthetic B2B sales deals using Claude AI. Each deal includes a full timeline of calls, emails, and CRM notes with configurable parameters like industry, deal size, sentiment arc, champion entry, and outcome. Supports single deals, bulk generation, and longitudinal series.

---

## What it does

- Configures deal parameters (industry, size, complexity, stakeholders, etc.)
- Runs a 3-stage AI pipeline to generate company profiles, deal timelines, full event content, and internal Slack conversations
- Streams generation progress in real time via Server-Sent Events
- Stores deals as NDJson files and displays them in a browsable UI with timeline, sentiment arc, stakeholder grid, and Slack view
- Supports **bulk generation** of N randomized deals concurrently
- Supports **series deals** representing an account's evolution over months with extended dynamics
- Optionally generates **post-close Customer Success** scenarios with support tickets and calls
- Generates **internal Slack conversations** — realistic back-and-forth team threads tied to key deal moments

---

## Prerequisites

- Python 3.11+
- Node.js 18+
- An [Anthropic API key](https://console.anthropic.com/)

---

## Setup

### 1. Backend

```bash
cd backend
python3 -m venv venv
source venv/bin/activate       # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

Copy the environment file and add your API key:

```bash
cp .env.example .env
```

Open `backend/.env` and set:

```
ANTHROPIC_API_KEY=sk-ant-...
CLAUDE_MODEL=claude-haiku-4-5-20251001   # optional override
```

### 2. Frontend

```bash
cd frontend
npm install
```

Copy the environment file (defaults point to `localhost:8000` — no changes needed for local dev):

```bash
cp .env.example .env
```

---

## Running the app

### Start the backend

```bash
cd backend
source venv/bin/activate       # Windows: venv\Scripts\activate
uvicorn main:app --reload --port 8000
```

Backend runs at `http://localhost:8000`. Interactive API docs at `http://localhost:8000/docs`.

### Start the frontend

In a separate terminal:

```bash
cd frontend
npm run dev
```

Frontend runs at `http://localhost:5173`. Open that URL in your browser.

### Stop the servers

Press `Ctrl+C` in each terminal. If a port stays in use:

```bash
lsof -ti :8000 | xargs kill -9   # backend
lsof -ti :5173 | xargs kill -9   # frontend
```

---

## Generating deals

### Single deal

1. Click **+ New Deal** in the sidebar
2. Fill in the configuration form:
   - **Company Name** — leave blank to auto-generate
   - **Industry** — e.g. Fintech, Healthcare Tech, Cybersecurity
   - **Deal Size** — e.g. `$75k ARR`
   - **Sales Cycle** — 14–180 days
   - **Starting / Ending Sentiment** — positive, neutral, concerned, negative
   - **Deal Outcome** — Closed Won or Closed Lost
   - **Champion Entry** — when (or if) a champion emerges during the cycle
   - **Main Objection** — e.g. Security Review, Budget Approval
   - **Buyer Urgency** — low, medium, high
   - **Calls / Emails per Stage / Stakeholders** — event density controls
   - **Complexity** — simple, normal, messy
   - **AE Name / SE Name** — leave blank to auto-generate
   - **Business Use Case** — optional context that shapes objections and stakeholder archetypes
3. Click **Generate Deal** and watch the progress bar
4. Click **Stop** at any time to cancel

### Customer Success scenario

Enable the **CS Scenario** toggle in the form to append post-close support events:

- **Adoption Challenge** — integration complexity, training gap, workflow mismatch, performance issues, unclear ROI
- **Support Contact Frequency** — how often the customer opens tickets
- **Churn Probability** — 0.0–1.0, shapes the support narrative
- **Post-Close Days** — how many days of CS activity to generate (7–180)

CS events are generated as support tickets and support calls appended to the deal timeline after the close date.

### Slack view

Every generated deal includes a **Slack** tab in the deal view. The tab shows internal team conversations generated alongside the deal:

- Channels are named `#deal-{company}` (simple/normal) or include `#at-risk` and `#escalations` (messy complexity)
- Messages are back-and-forth threads — AE posts after a call, Manager or SE replies, others chime in
- Senders are labeled by role (AE, SE, Manager, SDR, Legal, CS) with their real names pulled from the deal configuration
- Thread replies are visually nested under their parent message
- Series deals generate a single focused deal channel; standard deals may produce multiple channels based on complexity

### Series deals

Switch to the **Series** tab to generate a deal that represents an account's evolution over time:

- **Account Age (months)** — how long the account has existed
- **Touchpoint Frequency** — daily, weekly, biweekly, or monthly
- **Extended dynamics** — sales cycle velocity, procurement delay days, eval iteration count, champion replacement, discount percentage, win/loss reason, customer company size, competing vendors, and more

### Bulk generation

Switch to the **Bulk** tab to generate N random deals at once:

- Set a count and optionally lock specific variables (e.g. always Fintech, randomize everything else)
- Deals are generated 2 at a time with a shared rate limiter
- Real-time progress streams per deal as each completes

---

## Generation pipeline

Each deal goes through three stages:

| Stage | What it does | Output |
|-------|-------------|--------|
| **Stage 1 — Foundation** | Company profile, stakeholders, sentiment arc, objections | ~4K tokens |
| **Stage 2 — Timeline scaffold** | Ordered event metadata (calls, emails, CRM notes) in chunks | ~12K tokens |
| **Stage 3 — Content** | Full transcripts, email bodies, CRM notes — generated concurrently with cached context | ~2K tokens/event |
| **Stage 3 — Slack** | Internal Slack channels with threaded team conversations anchored to deal events | ~6K tokens |

Stage 3 runs up to 2 events concurrently with an output token rate limiter (10K tokens/min for Haiku) to stay within API limits. The deal context is cached in the system prompt block across all Stage 3 calls, reducing cost on larger deals. Slack generation runs after the timeline is complete and fails gracefully — the deal is saved even if Slack content cannot be produced.

---

## Deal storage

Generated deals are saved as `.ndjson` files in `backend/deals/`. Each file has:

- **Line 1:** deal metadata — company, stakeholders, sentiment arc, stage progression, objections, outcome, CS scenario
- **Lines 2+:** timeline events (calls, emails, CRM notes, support tickets, support calls, slack_channel, slack_message) sorted by timestamp

Filename format: `{company_slug}_{deal_id_short}_{timestamp}.ndjson`

This directory is gitignored — deals are local to your machine.

---

## Cost

Deals are generated using Claude Haiku (fast, cheap). Estimated cost per deal:

| Deal size | Events | Approx. cost |
|-----------|--------|-------------|
| Small | ~20 | ~$0.05 |
| Medium | ~30 | ~$0.07 |
| Large | ~50 | ~$0.11 |
| Bulk (10 deals) | ~300 | ~$0.80 |

Prompt caching in Stage 3 reduces costs ~20–30% on deals with 30+ events.

---

## API endpoints

| Method | Endpoint | Purpose |
|--------|----------|---------|
| `POST` | `/api/generate-stream` | Generate single deal (SSE) |
| `POST` | `/api/generate-series-stream` | Generate series deal (SSE) |
| `POST` | `/api/bulk-generate-stream` | Generate N random deals (SSE) |
| `GET` | `/api/deals` | List all deals |
| `GET` | `/api/deals/{deal_id}` | Get full deal with events |
| `DELETE` | `/api/deals/{deal_id}` | Delete a deal |

---

## Stress Testing

To validate the system performs reliably across a wide range of parameters, concurrent loads, and edge cases, run the comprehensive stress testing suite:

```bash
cd backend
python tests/run_stress_tests.py
```

The suite covers:
- **Parameter edge cases:** Min/max inputs, all enum values, unicode, special characters
- **Concurrent load:** Multiple deals generated simultaneously
- **Output validation:** Deal structure, sentiment arcs, timeline ordering
- **Performance:** Generation time, token usage, cost estimation
- **Error resilience:** Invalid inputs, boundary conditions
- **Rate limiter & cache:** Concurrent request handling and cache effectiveness
- **Token budgets:** Stage-wise and total token usage limits
- **API vs direct:** Comparing API endpoint and direct generator output

For detailed guidance, see [Stress Testing Guide](./docs/stress-testing-guide.md).

Metrics and cost analysis are saved to `backend/tests/reports/`.

---

## Project structure

```
mock-deal-generator/
├── backend/
│   ├── main.py           # FastAPI routes + SSE streaming
│   ├── generator.py      # 3-stage LLM pipeline
│   ├── prompts.py        # Prompt templates for all stages
│   ├── models.py         # Pydantic request/response models
│   ├── file_handler.py   # NDJson read/write
│   ├── random_config.py  # Random config for bulk generation
│   ├── requirements.txt
│   └── .env.example
└── frontend/
    ├── src/
    │   ├── features/
    │   │   ├── ConfigForm/   # Single deal form + bulk/series panels
    │   │   ├── DealList/     # Sidebar + empty state
    │   │   └── DealView/     # Timeline, sentiment arc, stakeholder grid, Slack view
    │   ├── components/       # Shared UI components
    │   ├── context/          # DealContext (global state)
    │   └── utils/            # Axios API client
    ├── package.json
    └── .env.example
```
