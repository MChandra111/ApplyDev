import { useCallback, useRef, useState } from 'react'
import { streamAnalyze } from '../api/analyze'
import type { PipelineEvent, PipelineResult, StepStatus } from '../types/api'
import {
  INITIAL_STEP_STATE,
  PIPELINE_STEPS,
  type TrackedStepId,
} from '../lib/pipelineSteps'

function isTrackedStep(node: string): node is TrackedStepId {
  return PIPELINE_STEPS.some((step) => step.id === node)
}

/** Central hook for streaming analysis state — keeps App.tsx thin. */
export function useJobAnalysis() {
  const [stepStatus, setStepStatus] = useState(INITIAL_STEP_STATE)
  const [result, setResult] = useState<PipelineResult | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [isAnalyzing, setIsAnalyzing] = useState(false)
  const [jobId, setJobId] = useState<string | null>(null)
  const [activeJobUrl, setActiveJobUrl] = useState<string | null>(null)
  const abortRef = useRef<AbortController | null>(null)

  const reset = useCallback(() => {
    setStepStatus({ ...INITIAL_STEP_STATE })
    setResult(null)
    setError(null)
    setJobId(null)
  }, [])

  const applyEvent = useCallback((event: PipelineEvent) => {
    const { node, status } = event

    if (event.job_id) {
      setJobId((prev) => prev ?? event.job_id)
    }

    if (isTrackedStep(node)) {
      setStepStatus((prev) => ({
        ...prev,
        [node]:
          status === 'running'
            ? 'running'
            : status === 'done'
              ? 'done'
              : status === 'error'
                ? 'error'
                : prev[node],
      }))
    }

    if (node === 'pipeline') {
      if (status === 'running') {
        setIsAnalyzing(true)
      }
      if (status === 'done' && event.output) {
        setResult(event.output as PipelineResult)
        setIsAnalyzing(false)
      }
      if (status === 'error') {
        setError(event.error ?? 'Pipeline failed')
        setIsAnalyzing(false)
      }
    }
  }, [])

  const loadFromHistory = useCallback(
    (entry: { job_id: string; job_url: string; result?: PipelineResult; error?: string }) => {
      abortRef.current?.abort()
      reset()
      setJobId(entry.job_id)
      setActiveJobUrl(entry.job_url)
      setResult(entry.result ?? null)
      setError(entry.error ?? null)
      setStepStatus(
        Object.fromEntries(
          PIPELINE_STEPS.map((step) => [step.id, entry.result ? 'done' : 'error']),
        ) as Record<TrackedStepId, StepStatus>,
      )
    },
    [reset],
  )

  const analyze = useCallback(
    async (jobUrl: string, options?: { jdText?: string; companyName?: string }) => {
      abortRef.current?.abort()
      const controller = new AbortController()
      abortRef.current = controller

      reset()
      setIsAnalyzing(true)
      setActiveJobUrl(jobUrl)

      try {
        const { jobId: id } = await streamAnalyze(
          jobUrl,
          { ...options, signal: controller.signal },
          applyEvent,
          (id) => setJobId(id),
        )
        if (id) setJobId(id)
      } catch (err) {
        if (controller.signal.aborted) return
        const message = err instanceof Error ? err.message : 'Analysis failed'
        setError(message)
        setIsAnalyzing(false)
      }
    },
    [applyEvent, reset],
  )

  return {
    stepStatus,
    result,
    error,
    isAnalyzing,
    jobId,
    activeJobUrl,
    analyze,
    loadFromHistory,
    reset,
  }
}
