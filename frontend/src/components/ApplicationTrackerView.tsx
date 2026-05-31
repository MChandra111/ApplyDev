import { useMemo } from 'react'
import type { ApplicationStage, JobHistoryEntry } from '../types/api'
import {
  APPLICATION_STAGES,
  STAGE_META,
  groupJobsByApplicationStage,
} from '../lib/applicationStage'
import { getCompanyFromEntry, getJobTitleFromEntry } from '../lib/jobLabels'
import { ApplicationStagePicker, ApplicationStageTag } from './ApplicationStagePicker'

interface ApplicationTrackerViewProps {
  history: JobHistoryEntry[]
  onStageChange: (jobId: string, stage: ApplicationStage | undefined) => void
}

/** Kanban-style board of tagged jobs across Applied → Interviewing → Hired. */
export function ApplicationTrackerView({
  history,
  onStageChange,
}: ApplicationTrackerViewProps) {
  const groups = useMemo(() => groupJobsByApplicationStage(history), [history])
  const trackedCount = APPLICATION_STAGES.reduce(
    (total, stage) => total + groups[stage].length,
    0,
  )

  if (trackedCount === 0) {
    return (
      <div className="flex min-h-80 flex-col items-center justify-center rounded-xl border border-dashed border-border px-6 py-16 text-center">
        <p className="text-lg font-medium text-foreground">No tracked applications yet</p>
        <p className="mt-2 max-w-lg text-sm text-muted">
          Open a job on the <strong className="font-medium text-foreground">Saved Jobs</strong>{' '}
          tab and tag it as Applied, Interviewing, or Hired. Tagged jobs appear here in a
          pipeline board.
        </p>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <h2 className="text-lg font-semibold text-foreground">Application pipeline</h2>
          <p className="mt-1 text-sm text-muted">
            {trackedCount} {trackedCount === 1 ? 'job' : 'jobs'} across your active pipeline
          </p>
        </div>
        <div className="flex flex-wrap gap-3 text-sm">
          {APPLICATION_STAGES.map((stage) => (
            <span key={stage} className="flex items-center gap-2 text-muted">
              <ApplicationStageTag stage={stage} />
              <span className="font-mono">{groups[stage].length}</span>
            </span>
          ))}
        </div>
      </div>

      <div className="grid gap-4 lg:grid-cols-3">
        {APPLICATION_STAGES.map((stage) => (
          <TrackerColumn
            key={stage}
            stage={stage}
            jobs={groups[stage]}
            onStageChange={onStageChange}
          />
        ))}
      </div>
    </div>
  )
}

function TrackerColumn({
  stage,
  jobs,
  onStageChange,
}: {
  stage: ApplicationStage
  jobs: JobHistoryEntry[]
  onStageChange: (jobId: string, stage: ApplicationStage | undefined) => void
}) {
  const meta = STAGE_META[stage]

  return (
    <section
      className={`flex min-h-96 flex-col rounded-xl border ${meta.columnClass}`}
    >
      <header className="border-b border-border px-4 py-3">
        <div className="flex items-center justify-between gap-2">
          <h3 className="font-semibold text-foreground">{meta.label}</h3>
          <span className="rounded-full bg-background/60 px-2 py-0.5 text-xs text-muted">
            {jobs.length}
          </span>
        </div>
        <p className="mt-0.5 text-xs text-muted">{meta.description}</p>
      </header>

      <div className="flex-1 space-y-3 overflow-y-auto p-3">
        {jobs.length === 0 ? (
          <p className="px-2 py-6 text-center text-sm text-muted">
            No jobs in this stage
          </p>
        ) : (
          jobs.map((entry) => (
            <TrackerCard
              key={entry.job_id}
              entry={entry}
              onStageChange={onStageChange}
            />
          ))
        )}
      </div>
    </section>
  )
}

function TrackerCard({
  entry,
  onStageChange,
}: {
  entry: JobHistoryEntry
  onStageChange: (jobId: string, stage: ApplicationStage | undefined) => void
}) {
  const company = getCompanyFromEntry(entry)
  const jobTitle = getJobTitleFromEntry(entry)
  const score = entry.result?.opportunity_score

  return (
    <article className="rounded-lg border border-border bg-background/70 p-4 shadow-sm">
      <p className="text-xs font-semibold uppercase tracking-wide text-accent">
        {company}
      </p>
      <h4 className="mt-1 font-medium text-foreground">{jobTitle}</h4>

      <div className="mt-2 flex flex-wrap items-center gap-2 text-xs text-muted">
        <span>{formatDate(entry.created_at)}</span>
        {typeof score?.score === 'number' && (
          <span className="rounded bg-accent-subtle px-1.5 py-0.5 font-medium text-accent">
            {score.score}/10
          </span>
        )}
        {score?.recommendation && (
          <span className="uppercase">{score.recommendation}</span>
        )}
      </div>

      <div className="mt-3">
        <ApplicationStagePicker
          size="sm"
          value={entry.application_stage}
          onChange={(stage) => onStageChange(entry.job_id, stage)}
        />
      </div>

      <a
        href={entry.job_url}
        target="_blank"
        rel="noreferrer"
        className="mt-3 inline-block truncate text-xs text-muted hover:text-accent"
      >
        View posting →
      </a>
    </article>
  )
}

function formatDate(iso: string): string {
  try {
    return new Date(iso).toLocaleDateString(undefined, {
      month: 'short',
      day: 'numeric',
    })
  } catch {
    return iso
  }
}
