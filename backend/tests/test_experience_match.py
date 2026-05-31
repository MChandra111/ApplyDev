"""Unit tests for years-of-experience matching."""

from app.models.jd_parse import JDExperienceRequirement, JDSkillRequirement
from app.models.resume_profile import ResumeExperienceProfile, SkillExperienceEntry
from app.services.experience_match import (
    build_experience_match,
    build_full_experience_match,
    build_skill_experience_checks,
)
from app.rag.resume_profile import lookup_skill_years


def _sample_profile() -> ResumeExperienceProfile:
    return ResumeExperienceProfile(
        source_hash="test",
        generated_at="2025-01-01T00:00:00Z",
        total_years_professional=1.0,
        skill_experience=[
            SkillExperienceEntry(skill="React", years=1.0, evidence="Intern 2024"),
            SkillExperienceEntry(skill="Python", years=1.5, evidence="Intern + TA"),
        ],
    )


def test_not_specified_when_jd_silent() -> None:
    match = build_experience_match(None, 1.0)
    assert match.status == "not_specified"
    assert match.required_min_years is None


def test_meets_requirement() -> None:
    req = JDExperienceRequirement(min_years=3, raw_text="3+ years React")
    match = build_experience_match(req, 3.0)
    assert match.status == "meets"
    assert match.gap_years is None


def test_short_of_requirement() -> None:
    req = JDExperienceRequirement(min_years=5, raw_text="5+ years")
    match = build_experience_match(req, 1.0)
    assert match.status == "short"
    assert match.gap_years == 4.0


def test_per_skill_checks() -> None:
    profile = _sample_profile()
    skills = [
        JDSkillRequirement(
            skill="React",
            priority="required",
            evidence_query="react",
            min_years=3.0,
            experience_raw_text="3+ years React",
        ),
        JDSkillRequirement(
            skill="Python",
            priority="required",
            evidence_query="python",
            min_years=1.0,
            experience_raw_text="1+ years Python",
        ),
    ]
    checks = build_skill_experience_checks(skills, profile)
    assert len(checks) == 2
    assert checks[0].status == "short"
    assert checks[1].status == "meets"


def test_lookup_skill_fuzzy() -> None:
    profile = _sample_profile()
    assert lookup_skill_years(profile, "React.js") == 1.0
    assert lookup_skill_years(profile, "Go") == 0.0


def test_aggregate_short_if_any_skill_short() -> None:
    profile = _sample_profile()
    skills = [
        JDSkillRequirement(
            skill="React",
            priority="required",
            evidence_query="react",
            min_years=3.0,
            experience_raw_text="3+ years React",
        ),
    ]
    match = build_full_experience_match(None, skills, profile)
    assert match.status == "short"
    assert len(match.skill_checks) == 1
    assert match.skill_checks[0].skill == "React"
    assert "React" in match.summary
    assert "Experience gaps" not in match.summary


def test_aggregate_summary_lists_short_skills() -> None:
    profile = _sample_profile()
    skills = [
        JDSkillRequirement(
            skill="React",
            priority="required",
            evidence_query="react",
            min_years=3.0,
            experience_raw_text="3+ years React",
        ),
        JDSkillRequirement(
            skill="Go",
            priority="required",
            evidence_query="go",
            min_years=2.0,
            experience_raw_text="2+ years Go",
        ),
    ]
    match = build_full_experience_match(None, skills, profile)
    assert "2 requirements" in match.summary
    assert "React" in match.summary and "Go" in match.summary
