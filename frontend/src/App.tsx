import { useCallback, useEffect, useMemo, useState } from 'react'
import { checkBackendHealth } from './api/analyze'
import { AppHeader, type AppTab } from './components/AppHeader'
import { ApplicationTrackerView } from './components/ApplicationTrackerView'
import { DashboardView } from './components/DashboardView'
import { SavedJobsView } from './components/SavedJobsView'
import { countTrackedJobs } from './lib/applicationStage'
import { useJobAnalysis } from './hooks/useJobAnalysis'
import { createHistoryEntry, useJobHistory } from './hooks/useJobHistory'

function App() {
  const [activeTab, setActiveTab] = useState<AppTab>('analyze')
  const [backendOk, setBackendOk] = useState<boolean | null>(null)
  const {
    stepStatus,
    result,
    error,
    isAnalyzing,
    jobId,
    activeJobUrl,
    analyze,
  } = useJobAnalysis()
  const { history, addEntry, setApplicationStage, deleteJob } = useJobHistory()
  const trackedCount = countTrackedJobs(history)

  const savedEntryForCurrentJob = useMemo(
    () => (jobId ? history.find((entry) => entry.job_id === jobId) : undefined),
    [history, jobId],
  )

  const isSavedForLater = Boolean(savedEntryForCurrentJob)
  const isInTracker = Boolean(savedEntryForCurrentJob?.application_stage)

  const saveCurrentJob = useCallback(() => {
    if (!jobId || !activeJobUrl || !result) return
    addEntry(createHistoryEntry(jobId, activeJobUrl, 'completed', result))
    setActiveTab('saved')
  }, [jobId, activeJobUrl, result, addEntry])

  const markCurrentJobAsApplied = useCallback(() => {
    if (!jobId || !activeJobUrl || !result) return
    addEntry(createHistoryEntry(jobId, activeJobUrl, 'completed', result, undefined, 'applied'))
    setActiveTab('tracker')
  }, [jobId, activeJobUrl, result, addEntry])

  useEffect(() => {
    void checkBackendHealth().then(setBackendOk)
  }, [])

  return (
    <div className="min-h-screen bg-background text-foreground">
      <AppHeader
        activeTab={activeTab}
        onTabChange={setActiveTab}
        backendOk={backendOk}
        savedCount={history.length}
        trackedCount={trackedCount}
      />

      <main className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-10">
        {activeTab === 'analyze' && (
          <DashboardView
            stepStatus={stepStatus}
            result={result}
            error={error}
            isAnalyzing={isAnalyzing}
            onAnalyze={analyze}
            canSaveJob={Boolean(result && jobId && activeJobUrl)}
            isSaved={isSavedForLater}
            isTracked={isInTracker}
            onSaveJob={saveCurrentJob}
            onMarkApplied={markCurrentJobAsApplied}
          />
        )}
        {activeTab === 'saved' && (
          <SavedJobsView
            history={history}
            onStageChange={setApplicationStage}
            onDeleteJob={deleteJob}
          />
        )}
        {activeTab === 'tracker' && (
          <ApplicationTrackerView
            history={history}
            onStageChange={setApplicationStage}
          />
        )}
      </main>
    </div>
  )
}

export default App
