import type { StepStatus } from '../types/api'
import { PIPELINE_STEPS, type TrackedStepId } from '../lib/pipelineSteps'

interface PipelineStepsProps {
  stepStatus: Record<TrackedStepId, StepStatus>
}

/** CI/CD-style step list — each agent node shows pending → running → done. */
export function PipelineSteps({ stepStatus }: PipelineStepsProps) {
  return (
    <ol className="space-y-2">
      {PIPELINE_STEPS.map((step, index) => {
        const status = stepStatus[step.id]
        const prevStep = PIPELINE_STEPS[index - 1]
        const showParallelBranch =
          'parallel' in step &&
          step.parallel &&
          prevStep &&
          !('parallel' in prevStep && prevStep.parallel)

        return (
          <li key={step.id}>
            {showParallelBranch && (
              <p className="mb-2 ml-8 text-xs font-medium uppercase tracking-wider text-muted">
                Then in parallel
              </p>
            )}
            <div
              className={`flex items-center gap-3 rounded-lg border px-4 py-3 transition-colors ${
                status === 'running'
                  ? 'border-accent/50 bg-accent-subtle'
                  : status === 'done'
                    ? 'border-accent/40 bg-accent/10'
                    : status === 'error'
                      ? 'border-error/50 bg-error-subtle'
                      : 'border-border bg-background/40'
              }`}
            >
              <StepIcon status={status} />
              <div className="min-w-0 flex-1">
                <p className="text-sm font-medium text-foreground">{step.label}</p>
                <p className="text-xs text-muted">{statusLabel(status)}</p>
              </div>
              <code className="hidden text-xs text-muted sm:block">{step.id}</code>
            </div>
          </li>
        )
      })}
    </ol>
  )
}

function StepIcon({ status }: { status: StepStatus }) {
  if (status === 'running') {
    return (
      <span className="flex h-7 w-7 items-center justify-center">
        <svg className="h-5 w-5 animate-spin text-accent" viewBox="0 0 24 24" fill="none">
          <circle
            className="opacity-25"
            cx="12"
            cy="12"
            r="10"
            stroke="currentColor"
            strokeWidth="4"
          />
          <path
            className="opacity-75"
            fill="currentColor"
            d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"
          />
        </svg>
      </span>
    )
  }

  if (status === 'done') {
    return (
      <span className="flex h-7 w-7 items-center justify-center rounded-full bg-accent/20 text-accent">
        <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M5 13l4 4L19 7" />
        </svg>
      </span>
    )
  }

  if (status === 'error') {
    return (
      <span className="flex h-7 w-7 items-center justify-center rounded-full bg-error/20 text-error">
        <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M6 18L18 6M6 6l12 12" />
        </svg>
      </span>
    )
  }

  return (
    <span className="flex h-7 w-7 items-center justify-center rounded-full border border-border text-muted">
      <span className="h-2 w-2 rounded-full bg-muted" />
    </span>
  )
}

function statusLabel(status: StepStatus): string {
  switch (status) {
    case 'pending':
      return 'Waiting'
    case 'running':
      return 'Running…'
    case 'done':
      return 'Complete'
    case 'error':
      return 'Failed'
  }
}
