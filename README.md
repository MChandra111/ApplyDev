# ApplyDev

Multi-agent job application research system — researches companies, matches your resume, and generates tailored application materials.

**Status:** Phase 5 (React dashboard with SSE streaming UI)

## Project structure

```
ApplyDev/
├── backend/          # FastAPI API (agents, streaming, health)
│   ├── app/
│   │   ├── main.py
│   │   ├── agents/   # LLM agents (research, JD parse, writer, eval)
│   │   ├── graph/    # LangGraph state + nodes + pipeline
│   │   ├── tools/    # Callable tools (Tavily search, JD scrape, …)
│   │   ├── rag/      # Chunking, embeddings, Pinecone, retrieval
│   │   └── models/   # Pydantic output schemas
│   ├── scripts/      # CLI test runners
├── documents/        # Resume + project .txt files for RAG
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/         # React + Vite + TypeScript + Tailwind
│   ├── src/
│   └── Dockerfile
├── docker-compose.yml
├── .env.example      # Copy to .env and fill in keys
└── README.md
```

## Prerequisites

- Python 3.12+
- Node.js 20+
- Docker Desktop (optional, for Compose)

## Local setup (without Docker)

### 1. Environment variables

```bash
cp .env.example .env
# Edit .env with your API keys (not required for /health in Phase 0)
```

### 2. Backend

```bash
cd backend
python -m venv .venv

# Windows PowerShell
.\.venv\Scripts\Activate.ps1

pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Health check: http://localhost:8000/health

### 3. Frontend

In a second terminal:

```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:5173 — the dashboard should show **Backend connected** when the API is running.

## Phase 1 — Run the ResearchAgent

From `backend/` with your `.env` at the repo root (needs `GROQ_API_KEY` and `TAVILY_API_KEY`):

```bash
.\.venv\Scripts\Activate.ps1
python scripts/run_research_agent.py "Anthropic"
```

You should see `Tool call: tavily_web_search` lines in the console, then a JSON summary with `company_size`, `recent_news`, `tech_stack_mentions`, and `red_flags`.

## Phase 2 — RAG pipeline

**Prerequisite:** Add `PINECONE_API_KEY` to `.env` ([free starter tier](https://www.pinecone.io/)). Replace `documents/*.txt` with your real resume and projects.

```powershell
cd backend
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt

# 1) Chunk, embed (Pinecone Inference), and upsert
python scripts/ingest_documents.py

# 2) Acceptance test — should PASS with Heirmeios load-time bullet
python scripts/test_retrieval.py "React performance optimization"

# 3) Parse a JD and match each skill to resume chunks
python scripts/run_jd_parser.py
```

**Embeddings note:** Anthropic does not ship a public embeddings API like OpenAI’s. This project uses **Pinecone Inference** (`llama-text-embed-v2`) so you only need `PINECONE_API_KEY` — a common production pattern.

## Phase 3 — LangGraph pipeline

Runs six nodes in order with **parallel** research + JD parsing after scrape:

`scrape_jd` → (`research_company` ∥ `parse_jd`) → `write_bullets` → `write_cover_letter` → `evaluate_opportunity`

**Prerequisites:** `GROQ_API_KEY`, `TAVILY_API_KEY`, `PINECONE_API_KEY`, documents ingested (Phase 2). Optional: `LANGSMITH_API_KEY` for traces at [smith.langchain.com](https://smith.langchain.com).

```powershell
cd backend
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt

# First run — built-in sample JD (skips scraping)
python scripts/run_pipeline.py --company Cloudflare

# Or paste a saved posting into a .txt file
python scripts/run_pipeline.py --jd-file path\to\posting.txt --company Cloudflare

# Real URL (may fail if the site blocks bots)
python scripts/run_pipeline.py "https://jobs.lever.co/example/role-id"
```

You should see six `agent_logs` lines ending with `evaluate_opportunity: score=N/10`, plus resume bullets and cover letter in the JSON output.

## Phase 4 — Streaming API

Restart the backend after pulling changes so routes are loaded:

```powershell
cd backend
.\.venv\Scripts\Activate.ps1
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

| Endpoint | Purpose |
|----------|---------|
| `POST /api/analyze` | Run pipeline; response is **SSE** (`text/event-stream`) |
| `GET /api/jobs/{job_id}` | Fetch completed/failed result (header `X-Job-Id` on analyze) |

**Request body** (`POST /api/analyze`):

```json
{
  "job_url": "https://example.com/jobs/123",
  "jd_text": "optional — skips scrape for testing",
  "company_name": "optional — override inferred company"
}
```

**SSE event shape:**

```json
{ "job_id": "...", "node": "parse_jd", "status": "running|done|error", "output": {}, "error": null }
```

Smoke test (server must be running):

```powershell
python scripts/test_analyze_api.py --jd-text --company Cloudflare
```

Then open `GET http://localhost:8000/api/jobs/{job_id}` using the id printed as `X-Job-Id`.

## Phase 5 — React dashboard

With backend and frontend running (`npm run dev` in `frontend/`), open http://localhost:5173.

1. Paste a job URL (or use **Dev options** → sample JD to skip scraping).
2. Click **Analyze job** — the left column shows each agent step go from waiting → spinner → checkmark.
3. When complete, the right column shows tabs: Research Summary, Resume Bullets, Cover Letter, Opportunity Score.
4. Completed runs auto-save to **Saved Jobs**, grouped by company and job title.
5. Tag any saved job as **Applied**, **Interviewing**, or **Hired** — tagged jobs appear on the **Application Tracker** kanban board.

**Tip:** Keep “Send sample JD text” enabled for local demos unless you have a scraper-friendly job URL.

## Local setup (Docker Compose)

From the repo root:

```bash
cp .env.example .env
docker compose up --build
```

- Backend: http://localhost:8000/health
- Frontend: http://localhost:5173

## Phase roadmap

| Phase | Focus |
|-------|--------|
| 0 | Monorepo scaffold, health endpoint, Docker Compose |
| 1 | Single research agent + Tavily |
| 2 | RAG / Pinecone resume matching + JDParserAgent |
| 3 | LangGraph multi-agent pipeline ✓ |
| 4 | SSE streaming API ✓ |
| 5 | React dashboard ✓ |
| 6 | Eval harness |
| 7 | AWS deploy |
| 8 | Portfolio polish |
