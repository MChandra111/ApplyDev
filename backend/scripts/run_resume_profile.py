"""Regenerate documents/resume_profile.json from resume text via LLM."""

import sys
from pathlib import Path

_BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(_BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(_BACKEND_ROOT))

from app.config import configure_logging, load_project_env
from app.rag.resume_profile import ensure_resume_profile


def main() -> None:
    """Force-refresh the cached YoE profile from documents/*.txt."""
    load_project_env()
    configure_logging()
    profile = ensure_resume_profile(force=True)
    print(f"\nTotal: {profile.total_years_professional:g} years professional")
    print(f"Skills tracked: {len(profile.skill_experience)}\n")
    for entry in profile.skill_experience:
        print(f"  {entry.skill}: {entry.years:g} yrs — {entry.evidence[:72]}")
    if profile.notes:
        print(f"\nNotes: {profile.notes}\n")


if __name__ == "__main__":
    main()
