import type { ApplicationStage, JobHistoryEntry, PipelineResult } from '../types/api'
import { getCompanyFromEntry, getJobTitleFromResult } from './jobLabels'

const STORAGE_KEY = 'applydev-job-history'
const MAX_ENTRIES = 20

/** Read saved analyses from localStorage (newest first). */
export function loadJobHistory(): JobHistoryEntry[] {
  try {
    const raw = localStorage.getItem(STORAGE_KEY)
    if (!raw) return []
    const parsed = JSON.parse(raw) as JobHistoryEntry[]
    return Array.isArray(parsed) ? parsed : []
  } catch {
    return []
  }
}

/** Persist a completed or failed run to localStorage. */
export function saveJobHistoryEntry(entry: JobHistoryEntry): JobHistoryEntry[] {
  const existing = loadJobHistory()
  const prior = existing.find((item) => item.job_id === entry.job_id)
  if (prior?.application_stage) {
    entry.application_stage = prior.application_stage
  }

  const next = existing.filter((item) => item.job_id !== entry.job_id)
  next.unshift(entry)
  const trimmed = next.slice(0, MAX_ENTRIES)
  localStorage.setItem(STORAGE_KEY, JSON.stringify(trimmed))
  return trimmed
}

/** Update application stage tag for one saved job. */
export function updateJobApplicationStage(
  jobId: string,
  stage: ApplicationStage | undefined,
): JobHistoryEntry[] {
  const next = loadJobHistory().map((entry) =>
    entry.job_id === jobId ? { ...entry, application_stage: stage } : entry,
  )
  localStorage.setItem(STORAGE_KEY, JSON.stringify(next))
  return next
}

/** Build a history row from a finished pipeline run. */
export function createHistoryEntry(
  jobId: string,
  jobUrl: string,
  status: 'completed' | 'failed',
  result?: PipelineResult,
  error?: string,
): JobHistoryEntry {
  const entry: JobHistoryEntry = {
    job_id: jobId,
    job_url: jobUrl,
    company_name: result?.company_name ?? result?.research_summary?.company_name,
    job_title: getJobTitleFromResult(result),
    application_stage: status === 'completed' ? 'applied' : undefined,
    status,
    created_at: new Date().toISOString(),
    result,
    error,
  }

  if (!entry.company_name) {
    entry.company_name = getCompanyFromEntry(entry)
  }

  return entry
}
