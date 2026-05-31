import type { OpportunityScore } from '../../types/api'

interface ScoreTabProps {
  score?: OpportunityScore
}

export function ScoreTab({ score }: ScoreTabProps) {
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
          : 'border-border bg-background/40'
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
