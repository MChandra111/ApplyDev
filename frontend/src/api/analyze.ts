import type { AnalyzeOptions, PipelineEvent } from '../types/api'

const API_URL = import.meta.env.VITE_API_URL ?? 'http://localhost:8000'

/** Parse `data: {...}\n\n` blocks from a Server-Sent Events response body. */
export async function* parseSseStream(
  body: ReadableStream<Uint8Array>,
): AsyncGenerator<PipelineEvent> {
  const reader = body.getReader()
  const decoder = new TextDecoder()
  let buffer = ''

  try {
    while (true) {
      const { done, value } = await reader.read()
      if (done) break

      buffer += decoder.decode(value, { stream: true })

      let boundary = buffer.indexOf('\n\n')
      while (boundary !== -1) {
        const block = buffer.slice(0, boundary)
        buffer = buffer.slice(boundary + 2)

        for (const line of block.split('\n')) {
          if (line.startsWith('data:')) {
            const json = line.slice(5).trim()
            if (json) {
              yield JSON.parse(json) as PipelineEvent
            }
          }
        }

        boundary = buffer.indexOf('\n\n')
      }
    }
  } finally {
    reader.releaseLock()
  }
}

export interface StreamAnalyzeResult {
  jobId: string
  events: PipelineEvent[]
}

/** POST /api/analyze and yield each SSE event as it arrives. */
export async function streamAnalyze(
  jobUrl: string,
  options: AnalyzeOptions = {},
  onEvent?: (event: PipelineEvent) => void,
): Promise<StreamAnalyzeResult> {
  const body: Record<string, string> = { job_url: jobUrl }
  if (options.jdText) body.jd_text = options.jdText
  if (options.companyName) body.company_name = options.companyName

  const response = await fetch(`${API_URL}/api/analyze`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
    signal: options.signal,
  })

  if (!response.ok) {
    const text = await response.text()
    throw new Error(text || `Analyze failed (${response.status})`)
  }

  const jobId = response.headers.get('x-job-id') ?? ''
  const events: PipelineEvent[] = []

  if (!response.body) {
    throw new Error('No response body from analyze stream')
  }

  for await (const event of parseSseStream(response.body)) {
    events.push(event)
    onEvent?.(event)
  }

  return { jobId, events }
}

/** Lightweight health check used on app load. */
export async function checkBackendHealth(): Promise<boolean> {
  try {
    const response = await fetch(`${API_URL}/health`)
    if (!response.ok) return false
    const data = (await response.json()) as { status?: string }
    return data.status === 'ok'
  } catch {
    return false
  }
}

export { API_URL }
