# ApplyDev

A multi-agent pipeline that researches a company, matches your real resume experience against a job posting, and drafts tailored resume bullets, a cover letter, and a fit score — for engineers tired of writing the same application from scratch every time.

## Why

Most "resume tailoring" tools either rewrite your resume with invented metrics or make you manually re-explain your experience for every posting. ApplyDev instead treats your resume and project write-ups as a **retrieval corpus**: every bullet it writes has to be grounded in a chunk it actually pulled back from your documents, with an explicit rule against inventing numbers. Company research, requirement parsing, and writing are split into separate small agents rather than one mega-prompt, so each step is inspectable and independently testable.

![ApplyDev dashboard screenshot or demo gif](docs/demo.gif)

## How it works

1. **Scrape or accept a job description** — pastes a URL and the scraper (`httpx` + BeautifulSoup) strips it to plain text, or you paste JD text directly to skip scraping entirely for sites that block bots.
2. **Research and parse run in parallel** — a `ResearchAgent` runs an observe → act loop against Tavily search to find company size, recent news, tech stack mentions, and red flags; a `JDParserAgent` extracts required skills and years-of-experience requirements and matches each one against your resume via Pinecone RAG.
3. **Bullets and cover letter are written from evidence, not vibes** — the `WriterAgent` only sees the retrieved resume chunks and parsed JD, is instructed to "never invent metrics," and returns bullets capped at 28 words each.
4. **An `EvalAgent` scores the opportunity 1–10** with reasoning, based on the research and requirement fit, before you decide whether it's worth applying.
5. **Every node streams live over SSE** — the dashboard shows each of the six pipeline steps flip from pending → running → done in a CI/CD-style step list as the backend actually executes them.
6. **Runs are saved and tracked** — completed analyses persist to the browser, get tagged Applied / Interviewing / Hired / Rejected, and show up on a kanban-style Application Tracker board.

A separate LLM-as-judge eval harness (`evals/`) scores generated bullets against hand-written "ideal" bullets on relevance, specificity, and keyword match, so prompt changes can be checked for regressions before they ship (see `EVALS.md`).

## Tech stack

| Layer | Technology |
|---|---|
| Frontend | React 19, TypeScript, Vite, Tailwind CSS 4 |
| Backend | FastAPI, Python 3.12, Server-Sent Events |
| Orchestration | LangGraph (parallel fan-out/fan-in state graph) |
| AI / LLM | Groq (`llama-3.3-70b-versatile`) for all 5 agents (Research, JD Parser, Resume Profile, Writer, Eval) |
| Retrieval | Pinecone (vector store) + Pinecone Inference (`llama-text-embed-v2` embeddings) |
| Tools | Tavily (web search), BeautifulSoup4 + httpx (JD scraping) |
| Observability | LangSmith tracing (optional) |
| Storage | In-memory job store (backend), browser `localStorage` (job history/tracker) |
| Hosting | Docker Compose (backend + frontend containers) |
| Testing | pytest (unit), custom LLM-as-judge eval harness |

## Architecture notes

LangGraph's `astream()` only emits an update *after* a node finishes — there's no built-in "node started" event — but the dashboard needs to show a spinner the moment a step begins, not just a checkmark when it ends. `pipeline_stream.py` solves this by synthesizing `running` events itself: when `scrape_jd` completes, it immediately emits `running` for both parallel branches (`research_company`, `parse_jd`); when *both* of those report done, it emits `running` for `write_bullets`, and so on down the chain. This keeps the UI's step-by-step feel without needing a second event stream from LangGraph, at the cost of the stream module having to hardcode the graph's shape (`PARALLEL_NODES`, `SEQUENTIAL_AFTER_PARALLEL`) rather than deriving it from the graph definition — a reasonable tradeoff for a six-node pipeline that would need revisiting if the graph got significantly more dynamic.

## Getting started

**Prerequisites:** Python 3.12+, Node.js 20+, and (optionally) Docker Desktop.

```bash
# 1. Environment variables
cp .env.example .env
# Fill in GROQ_API_KEY, TAVILY_API_KEY, PINECONE_API_KEY at minimum

# 2. Backend
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1   # Windows; use `source .venv/bin/activate` on macOS/Linux
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# 3. Frontend (second terminal)
cd frontend
npm install
npm run dev
```

Open `http://localhost:5173` — the header shows **Backend connected** once the API is reachable, then paste a job URL (or enable "Send sample JD text" in Dev options to skip scraping) and click **Analyze job**.

Before your first real analysis, replace the placeholder files in `documents/` with your own `resume.txt` and `project_*.txt`, then run:

```bash
cd backend
python scripts/ingest_documents.py
```

This chunks and embeds your documents into Pinecone and regenerates the cached years-of-experience profile used for skill matching.

**Or with Docker Compose** (from the repo root, after step 1 above): `docker compose up --build`.

## Roadmap / known limitations

- Job results live in an in-memory Python dict — they're lost on backend restart; no database yet.
- Job history and the Application Tracker are `localStorage`-only: no accounts, no sync across devices/browsers.
- JD scraping has no headless-browser fallback, so postings behind bot protection (LinkedIn, some ATS platforms) need to be pasted as text manually.
- The eval harness's LLM-as-judge and the agents it's grading both run on the same Groq model family — cross-model judging would catch more bias (noted as a caveat in `EVALS.md`).
- Per the project's own phase roadmap: eval CI integration, cloud deployment, and general polish are still open (Phases 7–8).
