# Mock Deal Generator

Generates realistic synthetic B2B sales deals using Claude AI. Each deal includes a full timeline of calls, emails, and CRM notes with configurable parameters like industry, deal size, sentiment arc, champion entry, and outcome.

---

## What it does

- Configures deal parameters (industry, size, complexity, stakeholders, etc.)
- Runs a 3-stage AI pipeline to generate company profiles, deal timelines, and full event content
- Streams generation progress in real time
- Stores deals as NDJson files and displays them in a browsable UI with timeline, sentiment arc, and stakeholder grid

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

Backend runs at `http://localhost:8000`. API docs available at `http://localhost:8000/docs`.

### Start the frontend

In a separate terminal:

```bash
cd frontend
npm run dev
```

Frontend runs at `http://localhost:5173`. Open that URL in your browser.

---

## Generating a deal

1. Click **+ New Deal** in the sidebar
2. Fill in the configuration form:
   - **Company Name** — leave blank to auto-generate
   - **Industry** — e.g. Fintech, Healthcare Tech, Cybersecurity
   - **Deal Size** — e.g. `$75k ARR`
   - **Sales Cycle** — 14–180 days
   - **Starting / Ending Sentiment** — positive, neutral, concerned, negative
   - **Deal Outcome** — Closed Won or Closed Lost
   - **Champion Entry** — when (or if) a champion emerges
   - **Main Objection** — e.g. Security Review, Budget Approval
   - **Buyer Urgency** — low, medium, high
   - **Calls / Emails per Stage / Stakeholders** — event density controls
   - **Complexity** — simple, normal, messy
3. Click **Generate Deal** and watch the progress bar
4. Click **Stop** at any time to cancel generation

---

## Deal storage

Generated deals are saved as `.ndjson` files in `backend/deals/`. Each file has:
- **Line 1:** deal metadata (company, stakeholders, sentiment arc, stage progression)
- **Lines 2+:** timeline events (calls, emails, CRM notes) sorted by timestamp

This directory is gitignored — deals are local to your machine.

---

## Cost

Deals are generated using Claude Haiku (fast, cheap). Estimated cost per deal:

| Deal size | Events | Approx. cost |
|-----------|--------|-------------|
| Small | ~20 | ~$0.05 |
| Medium | ~30 | ~$0.07 |
| Large | ~50 | ~$0.11 |

---

## Project structure

```
mock-deal-generator/
├── backend/
│   ├── main.py           # FastAPI routes
│   ├── generator.py      # 3-stage LLM pipeline
│   ├── prompts.py        # Prompt templates
│   ├── models.py         # Pydantic models
│   ├── file_handler.py   # NDJson read/write
│   ├── requirements.txt
│   └── .env.example
└── frontend/
    ├── src/
    │   ├── features/     # ConfigForm, DealList, DealView
    │   ├── components/   # Shared UI components
    │   ├── context/      # DealContext (global state)
    │   └── utils/        # API client
    ├── package.json
    └── .env.example
```
