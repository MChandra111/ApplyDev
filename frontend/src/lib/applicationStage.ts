import type { ApplicationStage, JobHistoryEntry } from '../types/api'

export const APPLICATION_STAGES: ApplicationStage[] = [
  'applied',
  'interviewing',
  'hired',
]

export const STAGE_META: Record<
  ApplicationStage,
  { label: string; description: string; columnClass: string; tagClass: string }
> = {
  applied: {
    label: 'Applied',
    description: 'Application submitted',
    columnClass: 'border-border-accent bg-accent-subtle',
    tagClass: 'bg-accent-subtle text-foreground ring-accent/40',
  },
  interviewing: {
    label: 'Interviewing',
    description: 'In interview process',
    columnClass: 'border-border bg-surface',
    tagClass: 'bg-surface-raised text-foreground ring-accent/50',
  },
  hired: {
    label: 'Hired',
    description: 'Offer accepted',
    columnClass: 'border-accent/50 bg-accent/25',
    tagClass: 'bg-accent text-foreground ring-accent',
  },
}

/** Jobs with an application stage, grouped for the tracker board. */
export function groupJobsByApplicationStage(
  history: JobHistoryEntry[],
): Record<ApplicationStage, JobHistoryEntry[]> {
  const groups: Record<ApplicationStage, JobHistoryEntry[]> = {
    applied: [],
    interviewing: [],
    hired: [],
  }

  for (const entry of history) {
    if (entry.status !== 'completed' || !entry.application_stage) continue
    groups[entry.application_stage].push(entry)
  }

  for (const stage of APPLICATION_STAGES) {
    groups[stage].sort((a, b) => b.created_at.localeCompare(a.created_at))
  }

  return groups
}

export function countTrackedJobs(history: JobHistoryEntry[]): number {
  return history.filter(
    (entry) => entry.status === 'completed' && entry.application_stage,
  ).length
}
