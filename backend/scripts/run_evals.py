"""Phase 6 eval harness — run pipeline on test cases and LLM-judge resume bullets."""

import argparse
import json
import sys
from pathlib import Path

_BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(_BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(_BACKEND_ROOT))

from app.agents.bullet_judge_agent import BulletJudgeAgent
from app.config import configure_logging, get_repo_root, load_project_env
from app.graph.pipeline import run_pipeline
from app.graph.state import PipelineState
from app.models.bullet_eval import BulletJudgeScores, CaseEvalResult, EvalTestSuite

DEFAULT_SUITE_PATH = get_repo_root() / "evals" / "test_cases.json"


def load_test_suite(path: Path) -> EvalTestSuite:
    """Load and validate evals/test_cases.json."""
    raw = json.loads(path.read_text(encoding="utf-8"))
    return EvalTestSuite.model_validate(raw)


def average_dimension_scores(scores: BulletJudgeScores) -> float:
    """Compute mean of relevance, specificity, and keyword_match."""
    return round((scores.relevance + scores.specificity + scores.keyword_match) / 3, 2)


def run_case(case_id: str, suite: EvalTestSuite) -> CaseEvalResult:
    """Run full pipeline on one test case, then LLM-judge the bullets."""
    case = next((c for c in suite.cases if c.id == case_id), None)
    if case is None:
        msg = f"Unknown case id: {case_id}"
        raise ValueError(msg)

    initial: PipelineState = {
        "job_url": case.job_url,
        "jd_text": case.jd_text,
        "company_name": case.company_name,
        "agent_logs": [],
    }

    generated: list[str] = []
    job_title = case.name
    pipeline_error: str | None = None

    try:
        final = run_pipeline(initial)
        generated = final.get("resume_bullets") or []
        matched = final.get("matched_experience") or {}
        job_title = matched.get("job_title") or case.name
    except Exception as exc:
        pipeline_error = str(exc)

    if pipeline_error or not generated:
        scores = BulletJudgeScores(
            relevance=1,
            specificity=1,
            keyword_match=1,
            reasoning=(
                f"Pipeline failed or returned no bullets: {pipeline_error or 'empty output'}"
            ),
        )
        return CaseEvalResult(
            case_id=case.id,
            case_name=case.name,
            company_name=case.company_name,
            generated_bullets=generated,
            ideal_bullets=case.ideal_bullets,
            scores=scores,
            average_score=1.0,
            pipeline_error=pipeline_error,
        )

    judge = BulletJudgeAgent()
    scores = judge.score_bullets(
        job_title=job_title,
        company_name=case.company_name,
        jd_text=case.jd_text,
        ideal_bullets=case.ideal_bullets,
        generated_bullets=generated,
    )
    return CaseEvalResult(
        case_id=case.id,
        case_name=case.name,
        company_name=case.company_name,
        generated_bullets=generated,
        ideal_bullets=case.ideal_bullets,
        scores=scores,
        average_score=average_dimension_scores(scores),
    )


def _avg_score(results: list[CaseEvalResult]) -> float:
    """Suite-wide mean of per-case averages."""
    if not results:
        return 0.0
    return round(sum(r.average_score for r in results) / len(results), 2)


def print_report(results: list[CaseEvalResult], threshold: float) -> None:
    """Print per-case scores and suite summary to stdout."""
    print("\n" + "=" * 72)
    print("ApplyDev Eval Report — Resume Bullets (LLM-as-judge)")
    print("=" * 72)

    for result in results:
        s = result.scores
        status = "FAIL" if result.pipeline_error else "ok"
        print(f"\n[{result.case_id}] {result.case_name} @ {result.company_name} ({status})")
        print(f"  relevance={s.relevance}  specificity={s.specificity}  keyword_match={s.keyword_match}")
        print(f"  case average={result.average_score}/5.0")
        print(f"  reasoning: {s.reasoning}")
        if result.pipeline_error:
            print(f"  pipeline error: {result.pipeline_error}")
        print("  generated:")
        for bullet in result.generated_bullets:
            print(f"    • {bullet}")

    suite_avg = _avg_score(results)
    print("\n" + "-" * 72)
    print(f"Suite average: {suite_avg}/5.0  (pass threshold: {threshold})")
    if suite_avg < threshold:
        print(
            f"\n⚠ WARNING: Average score {suite_avg} is below {threshold}. "
            "Review writer prompts, RAG retrieval, or test-case ideal bullets.",
        )
    else:
        print(f"\n✓ Suite passed (average >= {threshold}).")
    print("=" * 72 + "\n")


def main() -> None:
    """CLI entry: run eval harness on all or one test case."""
    parser = argparse.ArgumentParser(
        description="Run ApplyDev Phase 6 eval harness (pipeline + LLM-as-judge)",
    )
    parser.add_argument(
        "--suite",
        type=Path,
        default=DEFAULT_SUITE_PATH,
        help=f"Path to test_cases.json (default: {DEFAULT_SUITE_PATH})",
    )
    parser.add_argument(
        "--case",
        dest="case_id",
        help="Run only this case id (e.g. frontend_react_cloudflare)",
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="List case ids and exit",
    )
    args = parser.parse_args()

    load_project_env()
    configure_logging()

    suite = load_test_suite(args.suite)

    if args.list:
        for case in suite.cases:
            print(f"  {case.id:30}  {case.name} @ {case.company_name}")
        return

    case_ids = [args.case_id] if args.case_id else [c.id for c in suite.cases]
    unknown = [cid for cid in case_ids if cid not in {c.id for c in suite.cases}]
    if unknown:
        print(f"Unknown case id(s): {', '.join(unknown)}", file=sys.stderr)
        sys.exit(1)

    print(f"Loaded {len(case_ids)} test case(s) from {args.suite}")
    print("Each case runs the full LangGraph pipeline (Tavily + Pinecone + Groq).\n")

    results: list[CaseEvalResult] = []
    for i, case_id in enumerate(case_ids, start=1):
        print(f"[{i}/{len(case_ids)}] Running {case_id}...")
        results.append(run_case(case_id, suite))

    print_report(results, suite.pass_threshold)

    if _avg_score(results) < suite.pass_threshold:
        sys.exit(1)


if __name__ == "__main__":
    main()
