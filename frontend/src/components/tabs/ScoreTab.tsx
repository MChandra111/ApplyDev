import type {
  ExperienceMatch,
  OpportunityScore,
  SkillExperienceCheck,
} from '../../types/api'

interface ScoreTabProps {
  score?: OpportunityScore
  experienceMatch?: ExperienceMatch
}

export function ScoreTab({ score, experienceMatch }: ScoreTabProps) {
  if (!score) {
    return <p className="text-sm text-muted">No opportunity score available.</p>
  }

  const recommendationStyle = recommendationClasses(score.recommendation)

  return (
    <div className="space-y-8">
      <div className="flex flex-col items-center gap-4 sm:flex-row sm:items-start">
        <ScoreRing value={score.score} />
        <div className="text-center sm:text-left">
          <p className="text-sm uppercase tracking-wide text-muted">Overall fit</p>
          <p className="text-3xl font-bold text-foreground">{score.score}/10</p>
          <span
            className={`mt-2 inline-block rounded-full px-3 py-1 text-xs font-semibold uppercase tracking-wide ${recommendationStyle}`}
          >
            {score.recommendation}
          </span>
        </div>
      </div>

      {experienceMatch && experienceMatch.status !== 'not_specified' && (
        <ExperienceMatchSection match={experienceMatch} />
      )}

      <div className="grid gap-4 md:grid-cols-3">
        <ReasonCard title="Fit" body={score.fit_summary} />
        <ReasonCard title="Growth" body={score.growth_summary} />
        <ReasonCard title="Red flags" body={score.red_flags_summary} accent="error" />
      </div>
    </div>
  )
}

function ScoreRing({ value }: { value: number }) {
  const clamped = Math.min(10, Math.max(1, value))
  const percent = (clamped / 10) * 100
  const circumference = 2 * Math.PI * 54
  const offset = circumference - (percent / 100) * circumference

  return (
    <div className="relative h-36 w-36 shrink-0">
      <svg className="h-full w-full -rotate-90" viewBox="0 0 120 120">
        <circle
          cx="60"
          cy="60"
          r="54"
          fill="none"
          stroke="currentColor"
          strokeWidth="10"
          className="text-border"
        />
        <circle
          cx="60"
          cy="60"
          r="54"
          fill="none"
          stroke="currentColor"
          strokeWidth="10"
          strokeLinecap="round"
          strokeDasharray={circumference}
          strokeDashoffset={offset}
          className="text-accent transition-all duration-700"
        />
      </svg>
      <div className="absolute inset-0 flex items-center justify-center">
        <span className="text-2xl font-bold text-foreground">{clamped}</span>
      </div>
    </div>
  )
}

function ExperienceMatchSection({ match }: { match: ExperienceMatch }) {
  const meets = match.status === 'meets'
  const border = meets ? 'border-accent/40 bg-accent-subtle' : 'border-error/40 bg-error-subtle'
  const label = meets ? 'Meets experience requirements' : 'Below experience requirements'
  const checks = match.skill_checks ?? []

  return (
    <article className={`rounded-lg border p-4 ${border}`}>
      <div className="flex flex-wrap items-center justify-between gap-2">
        <h4 className="text-xs font-semibold uppercase tracking-wide text-muted">
          Years of experience
        </h4>
        <span
          className={`rounded-full px-2.5 py-0.5 text-xs font-semibold uppercase ${
            meets ? 'bg-accent-subtle text-accent' : 'bg-error-subtle text-error'
          }`}
        >
          {label}
        </span>
      </div>
      <p className="mt-2 text-sm leading-relaxed text-foreground/90">{match.summary}</p>
      <p className="mt-2 text-xs text-muted">
        Overall profile: ~{match.candidate_years} yrs professional
      </p>

      {checks.length > 0 && (
        <ul className="mt-4 space-y-2 border-t border-border/60 pt-3">
          {checks.map((check) => (
            <SkillExperienceRow key={`${check.skill}-${check.raw_text}`} check={check} />
          ))}
        </ul>
      )}
    </article>
  )
}

function SkillExperienceRow({ check }: { check: SkillExperienceCheck }) {
  const meets = check.status === 'meets'

  return (
    <li className="flex flex-wrap items-center justify-between gap-2 text-sm">
      <div className="min-w-0">
        <p className="font-medium text-foreground">{check.skill}</p>
        <p className="text-xs text-muted">{check.summary}</p>
      </div>
      <span
        className={`shrink-0 rounded px-2 py-0.5 text-xs font-medium uppercase ${
          meets ? 'bg-accent-subtle text-accent' : 'bg-error-subtle text-error'
        }`}
      >
        {meets ? 'Meets' : 'Short'}
      </span>
    </li>
  )
}

function ReasonCard({
  title,
  body,
  accent,
}: {
  title: string
  body: string
  accent?: 'error'
}) {
  return (
    <article
      className={`rounded-lg border p-4 ${
        accent === 'error'
          ? 'border-error/30 bg-error-subtle'
          : 'border-border bg-surface shadow-sm'
      }`}
    >
      <h4 className="mb-2 text-xs font-semibold uppercase tracking-wide text-muted">
        {title}
      </h4>
      <p className="text-sm leading-relaxed text-foreground/90">{body}</p>
    </article>
  )
}

function recommendationClasses(recommendation: string): string {
  switch (recommendation.toLowerCase()) {
    case 'apply':
      return 'bg-accent-subtle text-accent'
    case 'maybe':
      return 'bg-surface-raised text-foreground ring-1 ring-accent/40'
    case 'pass':
      return 'bg-error-subtle text-error'
    default:
      return 'bg-surface-raised text-muted'
  }
}
