# ApplyDev Eval Harness (Phase 6)

This document describes how we measure **resume bullet quality** for the ApplyDev pipeline — not just “does the code run,” but “does the AI output actually help you apply to jobs?”

---

## What problem does this solve?

Unit tests can assert that `write_bullets` returns a JSON list. They **cannot** tell you whether those bullets are good enough to put on a resume.

LLM outputs are non-deterministic: the same job posting might produce different wording each run. String matching (`assert "React" in bullet`) is brittle and misses paraphrases. An **eval harness** runs the real pipeline on fixed test inputs and scores the **quality** of the output.

---

## Architecture

```
evals/test_cases.json          ← 5 job postings + human-written “ideal” bullets
        │
        ▼
backend/scripts/run_evals.py   ← for each case: full LangGraph pipeline → judge
        │
        ├── run_pipeline()     ← scrape (skipped), research, parse, write_bullets, …
        └── BulletJudgeAgent   ← Groq LLM scores generated vs ideal (1–5)
        │
        ▼
Console report + exit code 1 if suite average < 3.5
```

---

## Test cases (`evals/test_cases.json`)

Each case includes:

| Field | Purpose |
|-------|---------|
| `id` | Stable name for `--case` filtering |
| `company_name` | Passed to ResearchAgent (Tavily) |
| `jd_text` | Full job description — **scraping is skipped** so evals are reproducible |
| `ideal_bullets` | Hand-written gold-standard bullets grounded in `documents/resume.txt` and project files |
| `notes` | What themes the judge should expect (for humans maintaining the suite) |

**Current suite (5 roles):**

1. `frontend_react_cloudflare` — React performance / FastAPI / AWS
2. `backend_python_stripe` — Python APIs, PostgreSQL, Postman
3. `ai_engineer_databricks` — LangGraph, RAG, Pinecone, evals
4. `fullstack_swe_notion` — React + REST full-stack
5. `cloud_engineer_aws_partner` — AWS EC2 automation, Docker, certification

When you change prompts or RAG documents, re-run evals. If scores drop, you have a regression signal before users see bad bullets.

---

## LLM-as-judge

**What it is:** A separate LLM call whose only job is to **grade** another LLM’s output. It receives:

- Job description excerpt  
- **Ideal** bullets (your reference)  
- **Generated** bullets (from the pipeline)  

It returns JSON scores 1–5 on three dimensions:

| Dimension | Question the judge answers |
|-----------|----------------------------|
| **Relevance** | Do bullets fit the role and real evidence (no invented metrics)? |
| **Specificity** | Are tools, numbers, and outcomes concrete? |
| **Keyword match** | Are JD terms used naturally? |

**Why not string match?**  
“Cut load time 38%” and “reduced initial load by 38%” should both pass. A judge understands semantic equivalence; `grep` does not.

**Why Groq here?**  
The rest of the dev stack uses Groq (`llama-3.3-70b-versatile`). The project prompt mentions Claude for final demos — you can swap the judge client to Anthropic later for stricter grading; the harness interface stays the same.

**Caveats (say these in interviews):**

- Judges can be lenient or inconsistent — use **relative** scores (before/after prompt changes), not absolute truth.
- Keep temperature low (0.1) for reproducibility.
- Golden bullets encode *your* resume; update them when `documents/` changes.

---

## Eval harness vs unit tests

| | Unit tests | Eval harness |
|---|------------|--------------|
| **Speed** | Milliseconds | Minutes (5× full pipeline + API calls) |
| **Cost** | Free | Tavily + Groq + Pinecone per case |
| **Checks** | Schema, logic, edge cases | Subjective output quality |
| **When** | Every commit / CI | Before prompt changes, weekly, or pre-release |

**You need both.** Unit tests guard code correctness; evals guard **product quality** for AI features.

---

## How to run

**Prerequisites:** Same as Phase 3 — `GROQ_API_KEY`, `TAVILY_API_KEY`, `PINECONE_API_KEY`, documents ingested.

```powershell
cd backend
.\.venv\Scripts\Activate.ps1

# List cases
python scripts/run_evals.py --list

# Full suite (~15–25 min, many API calls)
python scripts/run_evals.py

# Single case (faster iteration while tuning prompts)
python scripts/run_evals.py --case frontend_react_cloudflare
```

**What success looks like:**

- Each case prints `relevance`, `specificity`, `keyword_match`, and a short `reasoning`.
- **Suite average ≥ 3.5** → pass message and exit code 0.
- **Suite average < 3.5** → `⚠ WARNING` and exit code 1 (useful for CI later).

---

## Interpreting regressions

If scores drop after a change:

1. **RAG** — Did ingestion run? Wrong chunks retrieved for a skill?
2. **Writer prompt** — Too verbose, invented metrics, or ignoring evidence JSON?
3. **Research noise** — Irrelevant Tavily facts steering bullets off-topic?
4. **Test cases stale** — Resume updated but `ideal_bullets` not?

Run one case with `--case` and compare generated vs ideal bullets in the report before rewriting prompts.

---

## Future CI integration (Phase 7+)

- Run `--case frontend_react_cloudflare` on PRs (smoke eval, not full suite).
- Nightly job for all 5 cases.
- Store scores in a JSON artifact to graph trends over time.

---

## Resume bullet template

> Built an LLM-as-judge eval harness with 5 golden job scenarios, scoring generated resume bullets on relevance, specificity, and keyword alignment; integrated pass/fail gates (≥3.5/5) to catch prompt regressions before deployment.
