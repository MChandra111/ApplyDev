import type { JobHistoryEntry, PipelineResult } from '../types/api'

/** Pull the parsed job title from pipeline output. */
export function getJobTitleFromResult(result?: PipelineResult): string {
  const raw = result?.matched_experience
  if (raw && typeof raw === 'object' && 'job_title' in raw) {
    const title = raw.job_title
    if (typeof title === 'string' && title.trim()) {
      return title.trim()
    }
  }
  return 'Untitled role'
}

/** Resolve display company from a saved entry or its result payload. */
export function getCompanyFromEntry(entry: JobHistoryEntry): string {
  const name =
    entry.company_name?.trim() ||
    entry.result?.company_name?.trim() ||
    entry.result?.research_summary?.company_name?.trim()

  return name || 'Unknown company'
}

/** Job title for list rows — prefers stored field, falls back to result parsing. */
export function getJobTitleFromEntry(entry: JobHistoryEntry): string {
  if (entry.job_title?.trim()) {
    return entry.job_title.trim()
  }
  return getJobTitleFromResult(entry.result)
}

export interface CompanyJobGroup {
  company: string
  jobs: JobHistoryEntry[]
}

/** Group saved jobs by company, sorted A→Z with newest job first within each group. */
export function groupHistoryByCompany(history: JobHistoryEntry[]): CompanyJobGroup[] {
  const map = new Map<string, JobHistoryEntry[]>()

  for (const entry of history) {
    const company = getCompanyFromEntry(entry)
    const jobs = map.get(company) ?? []
    jobs.push(entry)
    map.set(company, jobs)
  }

  return Array.from(map.entries())
    .sort(([companyA], [companyB]) => companyA.localeCompare(companyB))
    .map(([company, jobs]) => ({
      company,
      jobs: [...jobs].sort((a, b) => b.created_at.localeCompare(a.created_at)),
    }))
}
