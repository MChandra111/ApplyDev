"""Compare JD years-of-experience requirements against the candidate profile."""

from app.models.jd_parse import (
    ExperienceMatchResult,
    ExperienceMatchStatus,
    JDExperienceRequirement,
    JDSkillRequirement,
    SkillExperienceCheck,
)
from app.models.resume_profile import ResumeExperienceProfile
from app.rag.resume_profile import lookup_skill_years


def _compare_years(
    required_min: float,
    candidate_years: float,
    *,
    skill: str,
    raw_text: str = "",
) -> SkillExperienceCheck:
    """Build a meets/short check with a short summary (details live in numeric fields)."""
    gap = round(required_min - candidate_years, 1)

    if candidate_years >= required_min:
        summary = f"{candidate_years:g} yrs — meets {required_min:g}+"
    else:
        summary = f"{candidate_years:g} / {required_min:g}+ yrs ({gap:g} short)"

    return SkillExperienceCheck(
        skill=skill,
        status="meets" if candidate_years >= required_min else "short",
        required_min_years=required_min,
        candidate_years=candidate_years,
        gap_years=None if candidate_years >= required_min else (gap if gap > 0 else None),
        raw_text=raw_text,
        summary=summary,
    )


def build_skill_experience_checks(
    skills: list[JDSkillRequirement],
    profile: ResumeExperienceProfile,
) -> list[SkillExperienceCheck]:
    """Compare per-skill JD YoE requirements against the resume profile."""
    checks: list[SkillExperienceCheck] = []

    for requirement in skills:
        if requirement.min_years is None:
            continue

        candidate_years = lookup_skill_years(profile, requirement.skill)
        checks.append(
            _compare_years(
                requirement.min_years,
                candidate_years,
                skill=requirement.skill,
                raw_text=requirement.experience_raw_text,
            ),
        )

    return checks


def build_experience_match(
    requirement: JDExperienceRequirement | None,
    candidate_years: float,
) -> ExperienceMatchResult:
    """Return role-level match status; ignores when JD does not specify YoE."""
    if requirement is None or requirement.min_years is None:
        return ExperienceMatchResult(
            status="not_specified",
            required_min_years=None,
            candidate_years=candidate_years,
            gap_years=None,
            summary="No overall years-of-experience requirement in the JD.",
        )

    check = _compare_years(
        requirement.min_years,
        candidate_years,
        skill="Overall",
        raw_text=requirement.raw_text,
    )
    return ExperienceMatchResult(
        status=check.status,
        required_min_years=check.required_min_years,
        candidate_years=check.candidate_years or candidate_years,
        gap_years=check.gap_years,
        summary=check.summary,
    )


def _worst_status(statuses: list[ExperienceMatchStatus]) -> ExperienceMatchStatus:
    """Pick the strictest status across multiple checks."""
    if "short" in statuses:
        return "short"
    if "meets" in statuses:
        return "meets"
    return "not_specified"


def _aggregate_summary(
    status: ExperienceMatchStatus,
    checks: list[SkillExperienceCheck],
) -> str:
    """One-line headline; per-requirement detail is in skill_checks."""
    if status == "not_specified":
        return "No years-of-experience requirements stated in the job description."
    if status == "meets":
        return "All stated experience requirements are met."

    short_names = [c.skill for c in checks if c.status == "short"]
    if len(short_names) == 1:
        return f"Below minimum for {short_names[0]}."
    return f"Below minimum for {len(short_names)} requirements: {', '.join(short_names)}."


def build_full_experience_match(
    global_requirement: JDExperienceRequirement | None,
    skills: list[JDSkillRequirement],
    profile: ResumeExperienceProfile,
) -> ExperienceMatchResult:
    """Combine role-level and per-skill YoE checks into one aggregate result."""
    role_match = build_experience_match(
        global_requirement,
        profile.total_years_professional,
    )
    skill_checks = build_skill_experience_checks(skills, profile)

    active_checks: list[SkillExperienceCheck] = []
    if (
        global_requirement is not None
        and global_requirement.min_years is not None
    ):
        active_checks.append(
            _compare_years(
                global_requirement.min_years,
                profile.total_years_professional,
                skill="Overall",
                raw_text=global_requirement.raw_text,
            ),
        )
    active_checks.extend(skill_checks)

    if not active_checks:
        return ExperienceMatchResult(
            status="not_specified",
            required_min_years=None,
            candidate_years=profile.total_years_professional,
            gap_years=None,
            summary=_aggregate_summary("not_specified", []),
            skill_checks=[],
        )

    aggregate_status = _worst_status([check.status for check in active_checks])

    return ExperienceMatchResult(
        status=aggregate_status,
        required_min_years=role_match.required_min_years,
        candidate_years=profile.total_years_professional,
        gap_years=role_match.gap_years,
        summary=_aggregate_summary(aggregate_status, active_checks),
        skill_checks=active_checks,
    )
