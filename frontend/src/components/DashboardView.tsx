import type { PipelineResult, StepStatus } from '../types/api'
import { JobUrlForm } from './JobUrlForm'
import { PipelineSteps } from './PipelineSteps'
import { ResultsPanel } from './ResultsPanel'
import type { TrackedStepId } from '../lib/pipelineSteps'

interface DashboardViewProps {
  stepStatus: Record<TrackedStepId, StepStatus>
  result: PipelineResult | null
  error: string | null
  isAnalyzing: boolean
  onAnalyze: (jobUrl: string, options?: { jdText?: string; companyName?: string }) => void
}

/** Main analyzer: URL input, live pipeline steps, and results. */
export function DashboardView({
  stepStatus,
  result,
  error,
  isAnalyzing,
  onAnalyze,
}: DashboardViewProps) {
  const showPipeline =
    isAnalyzing || Object.values(stepStatus).some((status) => status !== 'pending')

  return (
    <div className="grid gap-6 lg:grid-cols-[minmax(0,1fr)_minmax(0,1.1fr)]">
      <section className="space-y-6">
        <div className="rounded-xl border border-border bg-surface p-6">
          <h2 className="mb-4 text-sm font-semibold uppercase tracking-wide text-muted">
            New analysis
          </h2>
          <JobUrlForm isAnalyzing={isAnalyzing} onAnalyze={onAnalyze} />
        </div>

        {error && (
          <div className="rounded-xl border border-error/50 bg-error-subtle px-4 py-3 text-sm text-error">
            {error}
          </div>
        )}

        {showPipeline && (
          <div className="rounded-xl border border-border bg-surface p-6">
            <h2 className="mb-4 text-sm font-semibold uppercase tracking-wide text-muted">
              Agent pipeline
            </h2>
            <PipelineSteps stepStatus={stepStatus} />
          </div>
        )}
      </section>

      <section>
        {result ? (
          <ResultsPanel result={result} />
        ) : (
          <div className="flex h-full min-h-64 items-center justify-center rounded-xl border border-dashed border-border p-8 text-center text-sm text-muted">
            {isAnalyzing
              ? 'Streaming agent output… results appear here when the pipeline finishes.'
              : 'Run an analysis to see research, bullets, cover letter, and score.'}
          </div>
        )}
      </section>
    </div>
  )
}
