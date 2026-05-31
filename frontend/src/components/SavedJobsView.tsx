import { useEffect, useMemo, useState } from 'react'
import type { ApplicationStage, JobHistoryEntry } from '../types/api'
import {
  type CompanyJobGroup,
  getCompanyFromEntry,
  getJobTitleFromEntry,
  groupHistoryByCompany,
} from '../lib/jobLabels'
import { ApplicationStagePicker, ApplicationStageTag } from './ApplicationStagePicker'
import { ResultsPanel } from './ResultsPanel'

interface SavedJobsViewProps {
  history: JobHistoryEntry[]
  onStageChange: (jobId: string, stage: ApplicationStage | undefined) => void
  onDeleteJob: (jobId: string) => void
}

/** Browse past analyses grouped by company, then job title. */
export function SavedJobsView({ history, onStageChange, onDeleteJob }: SavedJobsViewProps) {
  const groups = useMemo(() => groupHistoryByCompany(history), [history])
  const [selectedId, setSelectedId] = useState<string | null>(null)
  const [expandedCompanies, setExpandedCompanies] = useState<Set<string>>(
    () => new Set(),
  )

  useEffect(() => {
    if (!selectedId) return
    if (history.some((entry) => entry.job_id === selectedId)) return
    setSelectedId(null)
  }, [history, selectedId])

  const selectJob = (jobId: string) => {
    setSelectedId(jobId)
    const entry = history.find((item) => item.job_id === jobId)
    if (!entry) return
    const company = getCompanyFromEntry(entry)
    setExpandedCompanies((prev) => {
      if (prev.has(company)) return prev
      const next = new Set(prev)
      next.add(company)
      return next
    })
  }

  const deleteJob = (jobId: string) => {
    onDeleteJob(jobId)
    if (selectedId === jobId) setSelectedId(null)
  }

  const selected = useMemo(
    () => history.find((entry) => entry.job_id === selectedId) ?? null,
    [history, selectedId],
  )

  if (history.length === 0) {
    return (
      <div className="flex min-h-80 flex-col items-center justify-center rounded-xl border border-dashed border-border px-6 py-16 text-center">
        <p className="text-lg font-medium text-foreground">No saved jobs yet</p>
        <p className="mt-2 max-w-md text-sm text-muted">
          After you analyze a job, click <strong className="font-medium text-foreground">Save job</strong>{' '}
          on the Analyze tab to keep it here while you tailor your resume.
        </p>
      </div>
    )
  }

  return (
    <div className="grid gap-6 lg:grid-cols-[minmax(0,340px)_minmax(0,1fr)]">
      <aside className="rounded-xl border border-border bg-surface shadow-sm">
        <div className="border-b border-border px-4 py-3">
          <div className="flex items-start justify-between gap-2">
            <div>
              <h2 className="text-sm font-semibold uppercase tracking-wide text-muted">
                By company
              </h2>
              <p className="mt-0.5 text-xs text-muted">
                {groups.length} {groups.length === 1 ? 'company' : 'companies'} ·{' '}
                {history.length} {history.length === 1 ? 'job' : 'jobs'}
              </p>
            </div>
            {groups.length > 1 && (
              <div className="flex shrink-0 gap-2 text-xs">
                <button
                  type="button"
                  onClick={() => setExpandedCompanies(new Set())}
                  className="text-muted underline-offset-2 hover:text-foreground hover:underline"
                >
                  Collapse all
                </button>
                <button
                  type="button"
                  onClick={() =>
                    setExpandedCompanies(new Set(groups.map((group) => group.company)))
                  }
                  className="text-muted underline-offset-2 hover:text-foreground hover:underline"
                >
                  Expand all
                </button>
              </div>
            )}
          </div>
        </div>

        <div className="max-h-[calc(100vh-16rem)] overflow-y-auto p-2">
          {groups.map((group) => (
            <CompanyGroupSection
              key={group.company}
              group={group}
              expanded={expandedCompanies.has(group.company)}
              selectedId={selectedId}
              onToggle={() =>
                setExpandedCompanies((prev) => {
                  const next = new Set(prev)
                  if (next.has(group.company)) next.delete(group.company)
                  else next.add(group.company)
                  return next
                })
              }
              onSelectJob={selectJob}
            />
          ))}
        </div>
      </aside>

      <section className="min-w-0 space-y-4">
        {selected ? (
          <>
            <SavedJobHeader
              entry={selected}
              onStageChange={(stage) => onStageChange(selected.job_id, stage)}
              onDelete={() => deleteJob(selected.job_id)}
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

function CompanyGroupSection({
  group,
  expanded,
  selectedId,
  onToggle,
  onSelectJob,
}: {
  group: CompanyJobGroup
  expanded: boolean
  selectedId: string | null
  onToggle: () => void
  onSelectJob: (jobId: string) => void
}) {
  const hasSelected = group.jobs.some((entry) => entry.job_id === selectedId)

  return (
    <section className="mb-1 last:mb-0">
      <button
        type="button"
        onClick={onToggle}
        aria-expanded={expanded}
        className={`flex w-full items-center gap-2 rounded-lg px-2 py-2 text-left transition hover:bg-surface-raised ${
          hasSelected && !expanded ? 'bg-accent-subtle/50 ring-1 ring-accent/30' : ''
        }`}
      >
        <ChevronIcon expanded={expanded} />
        <span className="min-w-0 flex-1 truncate text-xs font-semibold uppercase tracking-wider text-accent">
          {group.company}
        </span>
        <span className="shrink-0 rounded-full bg-surface-raised px-2 py-0.5 text-xs text-muted">
          {group.jobs.length}
        </span>
      </button>

      {expanded && (
        <ul className="mb-2 ml-1 space-y-0.5 border-l border-border pl-2 pt-1">
          {group.jobs.map((entry) => (
            <li key={entry.job_id}>
              <JobListItem
                entry={entry}
                selected={selectedId === entry.job_id}
                onSelect={() => onSelectJob(entry.job_id)}
              />
            </li>
          ))}
        </ul>
      )}
    </section>
  )
}

function ChevronIcon({ expanded }: { expanded: boolean }) {
  return (
    <svg
      className={`h-4 w-4 shrink-0 text-muted transition-transform ${expanded ? 'rotate-90' : ''}`}
      viewBox="0 0 20 20"
      fill="currentColor"
      aria-hidden
    >
      <path
        fillRule="evenodd"
        d="M7.21 14.77a.75.75 0 01.02-1.06L10.94 10 7.23 6.29a.75.75 0 111.04-1.08l4.24 4.25a.75.75 0 010 1.06l-4.24 4.24a.75.75 0 01-1.06-.02z"
        clipRule="evenodd"
      />
    </svg>
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
      className={`w-full rounded-md px-2.5 py-2 text-left transition ${
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
  onDelete,
}: {
  entry: JobHistoryEntry
  onStageChange: (stage: ApplicationStage | undefined) => void
  onDelete: () => void
}) {
  const company = getCompanyFromEntry(entry)
  const jobTitle = getJobTitleFromEntry(entry)
  const score = entry.result?.opportunity_score

  return (
    <div className="rounded-xl border border-border bg-surface px-5 py-4 shadow-sm">
      <p className="text-xs font-semibold uppercase tracking-wide text-accent">
        {company}
      </p>
      <h2 className="mt-1 text-xl font-semibold text-foreground">{jobTitle}</h2>

      {entry.status === 'completed' ? (
        <div className="mt-4">
          <p className="mb-2 text-xs font-medium uppercase tracking-wide text-muted">
            Application stage
          </p>
          <ApplicationStagePicker
            value={entry.application_stage}
            onChange={onStageChange}
            onDelete={onDelete}
          />
        </div>
      ) : (
        <div className="mt-4">
          <button
            type="button"
            onClick={onDelete}
            className="text-xs text-error underline-offset-2 hover:underline"
          >
            Delete this job
          </button>
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
