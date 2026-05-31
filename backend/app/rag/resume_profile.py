"""Load and auto-refresh the candidate YoE profile from documents/*.txt."""

import hashlib
import json
import logging
from pathlib import Path

from app.agents.resume_profile_agent import ResumeProfileAgent
from app.config import get_documents_dir, get_repo_root
from app.models.resume_profile import ResumeExperienceProfile, SkillExperienceEntry

logger = logging.getLogger(__name__)

_PROFILE_PATH = get_repo_root() / "documents" / "resume_profile.json"
_RESUME_GLOB = ("resume.txt", "project_*.txt")


def _load_document_bundle() -> tuple[str, str]:
    """Concatenate resume + project files for hashing and LLM input."""
    documents_dir = get_documents_dir()
    parts: list[str] = []
    paths: list[Path] = []

    resume = documents_dir / "resume.txt"
    if resume.is_file():
        paths.append(resume)

    paths.extend(sorted(documents_dir.glob("project_*.txt")))

    if not paths:
        msg = f"No resume.txt or project_*.txt found in {documents_dir}"
        raise FileNotFoundError(msg)

    for path in paths:
        parts.append(f"### {path.name}\n{path.read_text(encoding='utf-8').strip()}")

    combined = "\n\n".join(parts)
    content_hash = hashlib.sha256(combined.encode("utf-8")).hexdigest()[:16]
    return combined, content_hash


def _read_cached_profile() -> ResumeExperienceProfile | None:
    """Return cached profile from disk, or None if missing or invalid."""
    if not _PROFILE_PATH.is_file():
        return None
    try:
        data = json.loads(_PROFILE_PATH.read_text(encoding="utf-8"))
        return ResumeExperienceProfile.model_validate(data)
    except (json.JSONDecodeError, ValueError) as exc:
        logger.warning("Could not read resume_profile.json: %s", exc)
        return None


def _write_profile(profile: ResumeExperienceProfile) -> ResumeExperienceProfile:
    """Persist profile next to resume documents."""
    _PROFILE_PATH.write_text(
        profile.model_dump_json(indent=2),
        encoding="utf-8",
    )
    return profile


def ensure_resume_profile(*, force: bool = False) -> ResumeExperienceProfile:
    """Refresh YoE profile when resume files change (or when force=True)."""
    documents_text, content_hash = _load_document_bundle()

    if not force:
        cached = _read_cached_profile()
        if cached and cached.source_hash == content_hash:
            logger.debug("Resume profile cache hit (hash=%s)", content_hash)
            return cached

    logger.info("Regenerating resume YoE profile (hash=%s)", content_hash)
    agent = ResumeProfileAgent()
    profile = agent.extract(documents_text, content_hash)
    return _write_profile(profile)


def get_resume_profile() -> ResumeExperienceProfile:
    """Return cached profile, refreshing automatically if documents changed."""
    return ensure_resume_profile(force=False)


def get_candidate_years_experience() -> float:
    """Return total professional years from the auto-maintained profile."""
    return get_resume_profile().total_years_professional


def lookup_skill_years(profile: ResumeExperienceProfile, skill_label: str) -> float:
    """Find estimated years for a JD skill label (fuzzy match on profile skills)."""
    needle = skill_label.lower().strip()
    if not needle:
        return 0.0

    best: float | None = None
    for entry in profile.skill_experience:
        hay = entry.skill.lower().strip()
        if hay == needle or needle in hay or hay in needle:
            best = entry.years if best is None else max(best, entry.years)

    return best if best is not None else 0.0


def get_skill_experience_entries() -> list[SkillExperienceEntry]:
    """Return all per-skill YoE entries from the current profile."""
    return get_resume_profile().skill_experience
