import { useEffect, useRef, useState } from 'react'
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
  const { history, addEntry, setApplicationStage } = useJobHistory()
  const savedJobRef = useRef<string | null>(null)
  const trackedCount = countTrackedJobs(history)

  useEffect(() => {
    void checkBackendHealth().then(setBackendOk)
  }, [])

  useEffect(() => {
    if (!jobId || !activeJobUrl || savedJobRef.current === jobId) return
    if (isAnalyzing) return

    if (result) {
      addEntry(createHistoryEntry(jobId, activeJobUrl, 'completed', result))
      savedJobRef.current = jobId
      return
    }

    if (error) {
      addEntry(createHistoryEntry(jobId, activeJobUrl, 'failed', undefined, error))
      savedJobRef.current = jobId
    }
  }, [jobId, activeJobUrl, result, error, isAnalyzing, addEntry])

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
          />
        )}
        {activeTab === 'saved' && (
          <SavedJobsView history={history} onStageChange={setApplicationStage} />
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
