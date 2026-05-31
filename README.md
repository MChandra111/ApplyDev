# ApplyDev

Multi-agent job application research system — researches companies, matches your resume, and generates tailored application materials.

**Status:** Phase 0 (environment scaffold)

## Project structure

```
ApplyDev/
├── backend/          # FastAPI API (agents, streaming, health)
│   ├── app/
│   │   └── main.py   # App entry + /health
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
| 2 | RAG / Pinecone resume matching |
| 3 | LangGraph multi-agent pipeline |
| 4 | SSE streaming API |
| 5 | React dashboard |
| 6 | Eval harness |
| 7 | AWS deploy |
| 8 | Portfolio polish |
