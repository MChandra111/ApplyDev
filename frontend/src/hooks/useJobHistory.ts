import { useCallback, useState } from 'react'
import type { ApplicationStage, JobHistoryEntry } from '../types/api'
import {
  createHistoryEntry,
  deleteJobHistoryEntry,
  loadJobHistory,
  saveJobHistoryEntry,
  updateJobApplicationStage,
} from '../lib/jobHistory'

/** Manage saved job history backed by localStorage. */
export function useJobHistory() {
  const [history, setHistory] = useState<JobHistoryEntry[]>(() => loadJobHistory())

  const addEntry = useCallback((entry: JobHistoryEntry) => {
    setHistory(saveJobHistoryEntry(entry))
  }, [])

  const setApplicationStage = useCallback(
    (jobId: string, stage: ApplicationStage | undefined) => {
      setHistory(updateJobApplicationStage(jobId, stage))
    },
    [],
  )

  const deleteJob = useCallback((jobId: string) => {
    setHistory(deleteJobHistoryEntry(jobId))
  }, [])

  return { history, addEntry, setApplicationStage, deleteJob }
}

export { createHistoryEntry }
