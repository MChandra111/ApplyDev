import { type FormEvent, useState } from 'react'

interface JobUrlFormProps {
  isAnalyzing: boolean
  onAnalyze: (jobUrl: string, options?: { jdText?: string; companyName?: string }) => void
}

/** Job URL input + optional dev shortcuts for testing without scraping. */
export function JobUrlForm({ isAnalyzing, onAnalyze }: JobUrlFormProps) {
  const [jobUrl, setJobUrl] = useState('https://example.com/jobs/sample')
  const [useSampleJd, setUseSampleJd] = useState(true)
  const [companyName, setCompanyName] = useState('Cloudflare')

  const handleSubmit = (event: FormEvent) => {
    event.preventDefault()
    const trimmed = jobUrl.trim()
    if (!trimmed) return

    if (useSampleJd) {
      onAnalyze(trimmed, {
        companyName,
        jdText: SAMPLE_JD,
      })
      return
    }

    onAnalyze(trimmed)
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div>
        <label htmlFor="job-url" className="mb-1.5 block text-sm font-medium text-foreground">
          Job posting URL
        </label>
        <input
          id="job-url"
          type="url"
          required
          value={jobUrl}
          onChange={(event) => setJobUrl(event.target.value)}
          placeholder="https://jobs.lever.co/company/role-id"
          className="w-full rounded-lg border border-border bg-background px-4 py-2.5 text-foreground placeholder:text-muted focus:border-accent focus:outline-none focus:ring-1 focus:ring-accent"
          disabled={isAnalyzing}
        />
      </div>

      <details className="rounded-lg border border-border bg-background/80 px-4 py-3 text-sm text-muted">
        <summary className="cursor-pointer font-medium text-foreground">
          Dev options (skip scraping)
        </summary>
        <div className="mt-3 space-y-3">
          <label className="flex items-center gap-2">
            <input
              type="checkbox"
              checked={useSampleJd}
              onChange={(event) => setUseSampleJd(event.target.checked)}
              disabled={isAnalyzing}
              className="rounded border-border bg-surface text-accent accent-accent"
            />
            Send sample JD text (recommended for local testing)
          </label>
          {useSampleJd && (
            <div>
              <label htmlFor="company-name" className="mb-1 block text-xs uppercase tracking-wide">
                Company name
              </label>
              <input
                id="company-name"
                type="text"
                value={companyName}
                onChange={(event) => setCompanyName(event.target.value)}
                disabled={isAnalyzing}
                className="w-full rounded-md border border-border bg-background px-3 py-2 text-foreground"
              />
            </div>
          )}
        </div>
      </details>

      <button
        type="submit"
        disabled={isAnalyzing}
        className="inline-flex items-center gap-2 rounded-lg bg-accent px-5 py-2.5 text-sm font-semibold text-foreground transition hover:bg-accent-hover disabled:cursor-not-allowed disabled:opacity-50"
      >
        {isAnalyzing ? (
          <>
            <Spinner className="h-4 w-4" />
            Analyzing…
          </>
        ) : (
          'Analyze job'
        )}
      </button>
    </form>
  )
}

function Spinner({ className }: { className?: string }) {
  return (
    <svg className={`animate-spin ${className ?? ''}`} viewBox="0 0 24 24" fill="none">
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
  )
}

const SAMPLE_JD = `
Senior Frontend Engineer — Cloudflare
Requirements: React, TypeScript, Core Web Vitals, FastAPI, AWS, Docker.
Nice to have: LangGraph, RAG.
`.trim()
