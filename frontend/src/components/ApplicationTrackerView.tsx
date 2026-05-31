import { useMemo } from 'react'
import type { ApplicationStage, JobHistoryEntry } from '../types/api'
import {
  STAGE_META,
  TRACKER_BOARD_STAGES,
  groupJobsByApplicationStage,
} from '../lib/applicationStage'
import { getCompanyFromEntry, getJobTitleFromEntry } from '../lib/jobLabels'
import { ApplicationStagePicker, ApplicationStageTag } from './ApplicationStagePicker'

interface ApplicationTrackerViewProps {
  history: JobHistoryEntry[]
  onStageChange: (jobId: string, stage: ApplicationStage | undefined) => void
}

/** Kanban board for active pipeline stages; rejected count shown in the header only. */
export function ApplicationTrackerView({
  history,
  onStageChange,
}: ApplicationTrackerViewProps) {
  const groups = useMemo(() => groupJobsByApplicationStage(history), [history])
  const activeCount = TRACKER_BOARD_STAGES.reduce(
    (total, stage) => total + groups[stage].length,
    0,
  )
  const rejectedCount = groups.rejected.length
  const trackedCount = activeCount + rejectedCount

  if (trackedCount === 0) {
    return (
      <div className="flex min-h-80 flex-col items-center justify-center rounded-xl border border-dashed border-border px-6 py-16 text-center">
        <p className="text-lg font-medium text-foreground">No tracked applications yet</p>
        <p className="mt-2 max-w-lg text-sm text-muted">
          Click <strong className="font-medium text-foreground">I applied</strong> on the Analyze
          tab after you submit, or set a stage on a job in{' '}
          <strong className="font-medium text-foreground">Saved Jobs</strong>.
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
            {activeCount} {activeCount === 1 ? 'job' : 'jobs'} in active pipeline
          </p>
        </div>
        <div className="flex items-center gap-2 text-sm text-muted">
          <ApplicationStageTag stage="rejected" />
          <span className="font-mono font-medium text-foreground">{rejectedCount}</span>
        </div>
      </div>

      <div className="grid gap-4 lg:grid-cols-3">
        {TRACKER_BOARD_STAGES.map((stage) => (
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
          <span className="rounded-full bg-surface-raised px-2 py-0.5 text-xs text-muted">
            {jobs.length}
          </span>
        </div>
        <p className="mt-0.5 text-xs text-muted">{meta.description}</p>
      </header>

      <div className="flex-1 space-y-1.5 overflow-y-auto p-2">
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
  const scoreValue = entry.result?.opportunity_score?.score

  return (
    <article className="rounded-md border border-border bg-surface px-2.5 py-2 shadow-sm">
      <div className="flex items-start justify-between gap-2">
        <p className="min-w-0 truncate text-xs font-semibold uppercase tracking-wide text-accent">
          {company}
        </p>
        <div className="flex shrink-0 items-center gap-1.5 text-xs text-muted">
          <span>{formatDate(entry.created_at)}</span>
          {typeof scoreValue === 'number' && (
            <>
              <span aria-hidden>·</span>
              <span className="font-medium text-accent">{scoreValue}/10</span>
            </>
          )}
        </div>
      </div>

      <a
        href={entry.job_url}
        target="_blank"
        rel="noreferrer"
        className="mt-0.5 block truncate text-sm font-medium leading-snug text-foreground underline-offset-2 hover:text-accent hover:underline"
      >
        {jobTitle}
      </a>

      <div className="mt-1.5">
        <ApplicationStagePicker
          size="sm"
          value={entry.application_stage}
          onChange={(stage) => onStageChange(entry.job_id, stage)}
        />
      </div>
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
