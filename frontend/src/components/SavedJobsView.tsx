import { useEffect, useMemo, useState } from 'react'
import type { ApplicationStage, JobHistoryEntry } from '../types/api'
import {
  getCompanyFromEntry,
  getJobTitleFromEntry,
  groupHistoryByCompany,
} from '../lib/jobLabels'
import { ApplicationStagePicker, ApplicationStageTag } from './ApplicationStagePicker'
import { ResultsPanel } from './ResultsPanel'

interface SavedJobsViewProps {
  history: JobHistoryEntry[]
  onStageChange: (jobId: string, stage: ApplicationStage | undefined) => void
}

/** Browse past analyses grouped by company, then job title. */
export function SavedJobsView({ history, onStageChange }: SavedJobsViewProps) {
  const groups = useMemo(() => groupHistoryByCompany(history), [history])
  const [selectedId, setSelectedId] = useState<string | null>(
    () => history[0]?.job_id ?? null,
  )

  useEffect(() => {
    if (selectedId && history.some((entry) => entry.job_id === selectedId)) return
    setSelectedId(history[0]?.job_id ?? null)
  }, [history, selectedId])

  const selected = useMemo(
    () => history.find((entry) => entry.job_id === selectedId) ?? null,
    [history, selectedId],
  )

  if (history.length === 0) {
    return (
      <div className="flex min-h-80 flex-col items-center justify-center rounded-xl border border-dashed border-border px-6 py-16 text-center">
        <p className="text-lg font-medium text-foreground">No saved jobs yet</p>
        <p className="mt-2 max-w-md text-sm text-muted">
          Completed analyses are saved automatically, organized by company and job
          title. Run your first analysis on the Analyze tab.
        </p>
      </div>
    )
  }

  return (
    <div className="grid gap-6 lg:grid-cols-[minmax(0,340px)_minmax(0,1fr)]">
      <aside className="rounded-xl border border-border bg-surface">
        <div className="border-b border-border px-4 py-3">
          <h2 className="text-sm font-semibold uppercase tracking-wide text-muted">
            By company
          </h2>
          <p className="mt-0.5 text-xs text-muted">
            {groups.length} {groups.length === 1 ? 'company' : 'companies'} ·{' '}
            {history.length} {history.length === 1 ? 'job' : 'jobs'}
          </p>
        </div>

        <div className="max-h-[calc(100vh-16rem)] overflow-y-auto p-3">
          {groups.map((group) => (
            <section key={group.company} className="mb-4 last:mb-0">
              <h3 className="mb-2 px-2 text-xs font-semibold uppercase tracking-wider text-accent">
                {group.company}
              </h3>
              <ul className="space-y-1">
                {group.jobs.map((entry) => (
                  <li key={entry.job_id}>
                    <JobListItem
                      entry={entry}
                      selected={selectedId === entry.job_id}
                      onSelect={() => setSelectedId(entry.job_id)}
                    />
                  </li>
                ))}
              </ul>
            </section>
          ))}
        </div>
      </aside>

      <section className="min-w-0 space-y-4">
        {selected ? (
          <>
            <SavedJobHeader
              entry={selected}
              onStageChange={(stage) => onStageChange(selected.job_id, stage)}
            />
            {selected.status === 'completed' && selected.result ? (
              <ResultsPanel result={selected.result} />
            ) : (
              <div className="rounded-xl border border-error/50 bg-error-subtle px-5 py-4 text-sm text-error">
                {selected.error ?? 'This analysis did not complete successfully.'}
              </div>
            )}
          </>
        ) : (
          <div className="flex min-h-64 items-center justify-center rounded-xl border border-dashed border-border text-sm text-muted">
            Select a job to view its saved analysis.
          </div>
        )}
      </section>
    </div>
  )
}

function JobListItem({
  entry,
  selected,
  onSelect,
}: {
  entry: JobHistoryEntry
  selected: boolean
  onSelect: () => void
}) {
  const jobTitle = getJobTitleFromEntry(entry)
  const score = entry.result?.opportunity_score?.score

  return (
    <button
      type="button"
      onClick={onSelect}
      className={`w-full rounded-lg px-3 py-2.5 text-left transition ${
        selected
          ? 'bg-accent-subtle ring-1 ring-accent/40'
          : 'hover:bg-surface-raised'
      }`}
    >
      <p className="truncate text-sm font-medium text-foreground">{jobTitle}</p>
      <div className="mt-1 flex flex-wrap items-center gap-2 text-xs">
        {entry.application_stage && (
          <ApplicationStageTag stage={entry.application_stage} />
        )}
        <AnalysisStatusBadge status={entry.status} />
        {typeof score === 'number' && (
          <span className="font-medium text-accent">{score}/10</span>
        )}
        <span className="text-muted">{formatDate(entry.created_at)}</span>
      </div>
    </button>
  )
}

function SavedJobHeader({
  entry,
  onStageChange,
}: {
  entry: JobHistoryEntry
  onStageChange: (stage: ApplicationStage | undefined) => void
}) {
  const company = getCompanyFromEntry(entry)
  const jobTitle = getJobTitleFromEntry(entry)
  const score = entry.result?.opportunity_score

  return (
    <div className="rounded-xl border border-border bg-surface px-5 py-4">
      <p className="text-xs font-semibold uppercase tracking-wide text-accent">
        {company}
      </p>
      <h2 className="mt-1 text-xl font-semibold text-foreground">{jobTitle}</h2>

      {entry.status === 'completed' && (
        <div className="mt-4">
          <p className="mb-2 text-xs font-medium uppercase tracking-wide text-muted">
            Application stage
          </p>
          <ApplicationStagePicker
            value={entry.application_stage}
            onChange={onStageChange}
          />
        </div>
      )}

      <div className="mt-3 flex flex-wrap items-center gap-3 text-sm text-muted">
        <span>Analyzed {formatDate(entry.created_at)}</span>
        {score && (
          <span className="rounded-full bg-accent-subtle px-2.5 py-0.5 text-accent">
            Score {score.score}/10 · {score.recommendation}
          </span>
        )}
      </div>
      <a
        href={entry.job_url}
        target="_blank"
        rel="noreferrer"
        className="mt-2 inline-block truncate text-xs text-muted underline-offset-2 hover:text-accent hover:underline"
      >
        {entry.job_url}
      </a>
    </div>
  )
}

function AnalysisStatusBadge({ status }: { status: JobHistoryEntry['status'] }) {
  const classes =
    status === 'completed'
      ? 'bg-accent-subtle text-accent'
      : 'bg-error-subtle text-error'

  return (
    <span className={`rounded px-1.5 py-0.5 font-medium uppercase ${classes}`}>
      {status}
    </span>
  )
}

function formatDate(iso: string): string {
  try {
    return new Date(iso).toLocaleString(undefined, {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
      hour: 'numeric',
      minute: '2-digit',
    })
  } catch {
    return iso
  }
}
